import cv2
import svgwrite
from svgwrite.path import Path
from skimage.morphology import skeletonize
from skimage import img_as_ubyte
import tempfile
import requests
import io
from PIL import Image


# API Hugging Face
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
headers = {"Authorization": "Bearer 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"}


def create_temp_folder():
    temp_folder = tempfile.mkdtemp()
    return temp_folder

def contour_to_bezier(contour, epsilon=0.1):
    approx = cv2.approxPolyDP(contour, epsilon=epsilon, closed=False)
    points = [tuple(pt[0]) for pt in approx]

    if not points:
        return ""

    commands = ["M" + " ".join(map(str, points[0]))]
    for point in points[1:]:
        commands.append("L" + " ".join(map(str, point)))
    return " ".join(commands)


def find_contour_bbox(image):
    binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Инициализация начальных значений для области обрезки
    x_min = image.shape[1]
    y_min = image.shape[0]
    x_max = 0
    y_max = 0

    # Обновление области обрезки для каждого контура
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x + w)
        y_max = max(y_max, y + h)

    return x_min, y_min, x_max - x_min, y_max - y_min

def jpg_to_svg(input_path, output_path):
    # Загрузка изображения
    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    
    # Отражение изображения относительно оси Y
    image = cv2.flip(image, 0)
    
    image = cv2.GaussianBlur(image, (5, 5), 0)

    # Определение области обрезки
    crop_params = find_contour_bbox(image)
    
    if crop_params is not None:
        crop_x, crop_y, crop_width, crop_height = crop_params
        cropped_image = image[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]

        # Преобразование в SVG
        binary = cv2.adaptiveThreshold(cropped_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        skeleton = skeletonize(binary // 255)
        skeleton = img_as_ubyte(skeleton)

        contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        dwg = svgwrite.Drawing(output_path, profile='tiny', size=cropped_image.shape[::-1])

        for contour in contours:
            bezier_path = contour_to_bezier(contour)
            if bezier_path:
                dwg.add(Path(d=bezier_path, fill='none', stroke='black', stroke_width=1))

        dwg.save()

def get_svg_bounds(paths):
    x_values = []
    y_values = []
    
    for path in paths:
        for segment in path:
            x_values.append(segment.start.real)
            y_values.append(segment.start.imag)
            x_values.append(segment.end.real)
            y_values.append(segment.end.imag)
            
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    
    return x_min, x_max, y_min, y_max

def get_image_from_huggingface(description):

    payload = {"inputs": description}
    response = requests.post(API_URL, headers=headers, json=payload)
    return Image.open(io.BytesIO(response.content))


def print_difference(original, new):
    for item in original:
        if item not in new:
            print(item)

def remove_duplicates(input_list):
    seen = set()
    white_list = ["G01 X0 Y0", "M03S15", "M100", "M101", "M03S35"]
    output_list = []
    for item in input_list:
        if item not in seen:
            if item not in white_list: 
                seen.add(item)
            output_list.append(item)
    
    return output_list


def find_inverted_path(points, start_index):
    """
    Находит и возвращает индекс, где начинается инвертированный путь, начиная с start_index.
    Если инвертированный путь не найден, возвращает None.
    """
    for i in range(start_index + 1, len(points)):
        if points[i] == points[start_index]:
            # Возможное начало инвертированного пути найдено
            j, k = start_index, i
            while j >= 0 and k < len(points) and points[j] == points[k]:
                j -= 1
                k += 1
            # Если j достигает -1, это означает, что мы нашли полный инвертированный путь
            if j == -1:
                return i
    return None

def remove_inverted_paths(points):
    i = 0
    while i < len(points):
        inverted_start = find_inverted_path(points, i)
        if inverted_start:
            del points[inverted_start:inverted_start + i + 1]
            i = 0  # Начнем проверку с начала списка, так как удаление может влиять на последующие пути
        else:
            i += 1
    return points

def extract_coordinates(gcode_lines):
    """Извлекает координаты из строк G-code."""
    coordinates = []
    for line in gcode_lines:
        parts = line.split()
        x = float(parts[1][1:])
        y = float(parts[2][1:])
        coordinates.append((x, y))
    return coordinates

def generate_gcode(coordinates, feed_rate=1000):
    """Генерирует G-code из списка координат."""
    gcode = []
    for (x, y) in coordinates:
        gcode.append(f"G01 X{x:.2f} Y{y:.2f} F{feed_rate}")
    return gcode
