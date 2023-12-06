import tkinter as tk
from tkinter import filedialog
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


class GCodeVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image to G-code Visualizer")

        self.load_button = tk.Button(self, text="Load Image", command=self.load_image)
        self.load_button.pack(pady=20)

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = None

        self.scale_slider = tk.Scale(self, from_=0.5, to=2.0, resolution=0.01, orient=tk.HORIZONTAL, label="Scale", command=self.update_scale)
        self.scale_slider.set(1.0)
        self.scale_slider.pack(pady=20)

        self.invert_y_button = tk.Button(self, text="Invert Y", command=self.invert_y)
        self.invert_y_button.pack(pady=20)

        self.gcode = []
        self.paths = []
        self.inverted = False

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("All images", "*.svg;*.jpg;*.png;*.jpeg;*.bmp"), ("SVG files", "*.svg"), ("Raster images", "*.jpg;*.png;*.jpeg;*.bmp")])

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

                shutil.rmtree(temp_folder)

                self.generate_gcode()
                self.visualize_gcode()

                #Чистим пути
                clear_paths = []
                for path in self.paths:
                    if (path and path.end.real != path.end.imag): clear_paths.append(path)
                self.paths = clear_paths

            except Exception as e:
                print(f"Error: {e}")
                # Here, you can display a pop-up error message to the user using tkinter's messagebox.

    def generate_gcode(self):
        self.gcode = []

        self.gcode.append("M3S1600")
        
        for path in self.paths:
                      
            # 2. Move to the start of the path
            if path:
                start_x, start_y = path.start.real, path.start.imag
                self.gcode.append(f"G01 X{start_x:.2f} Y{start_y:.2f}")

                # 3. Drop the pen down
                self.gcode.append("M3S3300")

                for segment in path:
                    # 4. Move through the path
                    x, y = segment.end.real, segment.end.imag
                    if self.inverted:
                        y = -y
                    self.gcode.append(f"G01 X{x:.2f} Y{y:.2f}")
                
                # 5. Lift the pen at the end of the path
                self.gcode.append("M3S1600")

        # Print the gcode
        for line in self.gcode:
            print(f"{line}\n")

    def visualize_gcode(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots(figsize=(6, 6))
        
        segments = []
        segment = []
        for point in self.gcode:
            if "G01" in point:
                coords = point.split(" ")
                x = float(coords[1][1:])
                y = float(coords[2][1:])
                segment.append((x, y))
            elif "M3S1600" in point:  # Split segments only on pen up command
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

    def on_scroll(self, event):
        current_scale = self.scale_slider.get()
        if event.button == 'up':
            self.scale_slider.set(min(2.0, current_scale + 0.1))
        elif event.button == 'down':
            self.scale_slider.set(max(0.5, current_scale - 0.1))
        self.update_scale(None)

    def update_scale(self, scale_value):
        self.visualize_gcode()

    def invert_y(self):
        self.inverted = not self.inverted
        self.generate_gcode()
        self.visualize_gcode()


if __name__ == "__main__":
    app = GCodeVisualizer()
    app.mainloop()
