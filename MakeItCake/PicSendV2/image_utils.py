import cv2
import svgwrite
from svgwrite.path import Path
from skimage.morphology import skeletonize
from skimage import img_as_ubyte
import tempfile


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

def jpg_to_svg(input_path, output_path):
    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    skeleton = skeletonize(binary // 255)
    skeleton = img_as_ubyte(skeleton)

    contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    dwg = svgwrite.Drawing(output_path, profile='tiny', size=image.shape[::-1])

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
