import tkinter as tk
from tkinter import filedialog, Text
from svgpathtools import svg2paths
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cv2
import svgwrite
from skimage.morphology import skeletonize
from skimage import img_as_ubyte
from svgwrite.path import Path
import os
import tempfile
import shutil
import serial

def create_temp_folder():
    temp_folder = tempfile.mkdtemp()
    return temp_folder

def contour_to_bezier(contour, epsilon=2.5):
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



class GCodeVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image to G-code Visualizer")

        self.load_button = tk.Button(self, text="Load Image", command=self.load_image)
        self.load_button.pack(pady=20)

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gcode_text = Text(self, wrap=tk.NONE)
        self.gcode_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.gcode_text.bind("<Control-c>", self.copy_text)

        self.canvas = None

        self.scale_slider = tk.Scale(self, from_=0.5, to=2.0, resolution=0.01, orient=tk.HORIZONTAL, label="Scale", command=self.update_scale)
        self.scale_slider.set(1.0)
        self.scale_slider.pack(pady=20)

        self.invert_y_button = tk.Button(self, text="Invert Y", command=self.invert_y)
        self.invert_y_button.pack(pady=20)

        self.send_gcode_button = tk.Button(self, text="Send to Arduino", command=self.send_gcode_to_arduino)
        self.send_gcode_button.pack(pady=20)

        self.gcode = []
        self.paths = []
        self.inverted = False

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("All images", "*.svg;*.jpg;*.png;*.jpeg;*.bmp"), 
                                                        ("SVG files", "*.svg"), 
                                                        ("Raster images", "*.jpg;*.png;*.jpeg;*.bmp")])

        if file_path:
            temp_folder = create_temp_folder()
            temp_file_path = os.path.join(temp_folder, os.path.basename(file_path))
            shutil.copy(file_path, temp_file_path)

            try:
                if temp_file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    output_path = temp_file_path + "_converted.svg"
                    jpg_to_svg(temp_file_path, output_path)
                    self.paths, _ = svg2paths(output_path)
                else:
                    self.paths, _ = svg2paths(temp_file_path)

                # Масштабирование путей SVG
                MACHINE_MAX_X = 95
                MACHINE_MAX_Y = 95

                x_min, x_max, y_min, y_max = get_svg_bounds(self.paths)
                svg_width = x_max - x_min
                svg_height = y_max - y_min

                # Вычисляем коэффициент масштабирования
                scale_factor = min(MACHINE_MAX_X / svg_width, MACHINE_MAX_Y / svg_height)

                # Если коэффициент масштабирования больше 1, устанавливаем его равным 1,
                # чтобы изображение не увеличивалось больше своего исходного размера.
                scale_factor = min(scale_factor, 1) 

                self.paths = self.scale_paths(self.paths, scale_factor)

                # Генерация G-code с учетом масштабированных путей
                self.generate_gcode()

                # Визуализация G-code
                self.visualize_gcode()

                shutil.rmtree(temp_folder)

            except Exception as e:
                print(f"Error: {e}")
                # Здесь, вы можете отобразить всплывающее сообщение об ошибке пользователю, используя messagebox в tkinter.

    def generate_gcode(self):
        self.gcode = []
        feed_rate = 1000  # скорость подачи в мм/мин
        self.gcode.append('S3300\n')
        pen_down = False  # флаг для отслеживания состояния пера

        for path in self.paths:
            for index, segment in enumerate(path):
                x, y = segment.end.real, segment.end.imag
                if self.inverted:
                    y = -y

                # # Если это начало пути и перо поднято
                # if index == 0 and not pen_down:
                #     self.gcode.append("M3S3300")
                #     pen_down = True

                # Добавить координаты в G-code
                self.gcode.append(f"G1 X{x:.2f} Y{y:.2f} F{feed_rate}")

                # # Если это конец пути и перо опущено
                # if index == len(path) - 1 and pen_down:
                #     self.gcode.append("M3S1600")
                #     pen_down = False

        self.gcode_text.delete(1.0, tk.END)
        self.gcode_text.insert(tk.END, "\n".join(self.gcode))



    def visualize_gcode(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots(figsize=(6, 6))
        
        segments = []
        segment = []
        for point in self.gcode:
            if "G1" in point:
                coords = point.split(" ")
                x = float(coords[1][1:])
                y = float(coords[2][1:])
                segment.append((x, y))
            else:
                if segment:
                    segments.append(segment)
                    segment = []
        if segment:
            segments.append(segment)

        for segment in segments:
            xs, ys = zip(*segment)
            
            if len(xs) <= 1:
                continue

            ax.plot(xs, ys, '-b', linewidth=0.3)

        ax.set_aspect('equal', adjustable='box')
        ax.set_facecolor('white')

        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def scale_paths(self, paths, scale_factor):
        """Масштабирует пути SVG."""
        return [path.scaled(scale_factor) for path in paths]


    def send_gcode_to_arduino(self):
        ARDUINO_PORT = "COM5"
        BAUD_RATE = 115200

        try:
            with serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2) as ser:
                for line in self.gcode:
                    ser.write(f"{line}\n".encode())
                    response = ser.readline().decode().strip()
                    print(f"Sent: {line}. Received: {response}")
                    
                    if "error" in response:
                        print(f"Error detected in G-code: {line}. Stopping transmission.")
                        break
        except Exception as e:
            print(f"Error: {e}")

    def on_scroll(self, event):
        current_scale = self.scale_slider.get()
        if event.button == 'up':
            self.scale_slider.set(min(2.0, current_scale + 0.1))
        elif event.button == 'down':
            self.scale_slider.set(max(0.5, current_scale - 0.1))
        self.update_scale(None)

    def update_scale(self, scale_value):
    # Генерация G-code с учетом нового масштаба
        self.generate_gcode()

        # Визуализация обновленного G-code
        self.visualize_gcode()

        # Обновление содержимого текстового поля
        self.gcode_text.delete(1.0, tk.END)
        for line in self.gcode:
            self.gcode_text.insert(tk.END, line + '\n')

    def invert_y(self):
        self.inverted = not self.inverted
        self.generate_gcode()
        self.visualize_gcode()

    def copy_text(self, event):
        selected_text = self.gcode_text.selection_get()
        self.root.clipboard_clear()
        self.root.clipboard_append(selected_text)

    def run(self):
        self.gcode_text.pack()
        self.root.mainloop()

if __name__ == "__main__":
    app = GCodeVisualizer()
    app.mainloop()
