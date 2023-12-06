import os
import cv2
import svgwrite
from skimage.morphology import skeletonize
from skimage import img_as_ubyte
from svgwrite.path import Path
import sys
import shutil


def contour_to_bezier(contour, epsilon=2.5):
    """Преобразует контур в путь кривой Безье."""
    approx = cv2.approxPolyDP(contour, epsilon=epsilon, closed=False)
    points = [tuple(pt[0]) for pt in approx]

    if not points:
        return ""

    commands = ["M" + " ".join(map(str, points[0]))]
    for point in points[1:]:
        commands.append("L" + " ".join(map(str, point)))
    return " ".join(commands)


def jpg_to_svg(input_path, output_path):
    # Чтение изображения и преобразование в оттенки серого
    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

    # Применение размытия
    image = cv2.GaussianBlur(image, (5, 5), 0)

    # Применение адаптивного порога
    binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Скелетизация изображения
    skeleton = skeletonize(binary // 255)
    skeleton = img_as_ubyte(skeleton)

    # Поиск всех контуров
    contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # Создание SVG файла
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=image.shape[::-1])

    # Обход всех контуров и их добавление в SVG
    for contour in contours:
        bezier_path = contour_to_bezier(contour)
        if bezier_path:
            dwg.add(Path(d=bezier_path, fill='none', stroke='black', stroke_width=1))

    dwg.save()


if __name__ == "__main__":
    another_path = sys.argv[1].replace('\\', "/")

    filename = another_path[another_path.rfind("/"):another_path.rfind(".")]

    # Путь, куда файл будет перемещен
    destination_path = "C:/ass.jpg"

    # Перемещение файла
    shutil.copy(another_path, destination_path)

    jpg_to_svg(destination_path, 'C:/Users/IT-сектор/Desktop/' + filename + '.svg')

    os.remove(destination_path)
