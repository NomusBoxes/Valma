import tkinter as tk
from tkinter import filedialog, Text
from svgpathtools import svg2paths
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
from image_utils import create_temp_folder, jpg_to_svg, get_svg_bounds
import shutil
import os
import threading

MACHINE_MAX_X = 50
MACHINE_MAX_Y = 50


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

        self.send_gcode_button = tk.Button(self, text="Send to Arduino", command=self.start_send_gcode_thread)
        self.send_gcode_button.pack(pady=20)

        self.stop_gcode_button = tk.Button(self, text="Stop and Reset", command=self.stop_and_reset)
        self.stop_gcode_button.pack(pady=20)

        self.gcode = []
        self.paths = []
        self.inverted = False
        self.stop_flag = False  # Флаг для остановки отправки кода

    def start_send_gcode_thread(self):
        thread = threading.Thread(target=self.send_gcode_to_arduino)
        thread.start()

    def stop_and_reset(self):
        self.stop_flag = True  # Устанавливаем флаг для остановки отправки кода


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

        self.gcode.append("M3S1600")
        for path in self.paths:
                      
            # 2. Move to the start of the path
            if path:
                start_x, start_y = path.start.real, path.start.imag
                self.gcode.append(f"G01 X{start_x:.2f} Y{start_y:.2f} F1000")

                # 3. Drop the pen down
                self.gcode.append("M3S3300")
  

                for segment in path:
                    # 4. Move through the path
                    x, y = segment.end.real, segment.end.imag
                    if self.inverted:
                        y = -y
                    self.gcode.append(f"G01 X{x:.2f} Y{y:.2f} F1000")
                
                # 5. Lift the pen at the end of the path
                self.gcode.append("M3S1600")
        self.gcode.append("G01 X0 Y0")

        self.gcode_text.delete(1.0, tk.END)
        for line in self.gcode:
            self.gcode_text.insert(tk.END, line + '\n')

        #self.gcode.append("M3S1600 G01 X0 Y0")
        # # Print the gcode
        # for line in self.gcode:
        #     print(f"{line}\n")

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

    def scale_paths(self, paths, scale_factor):
        """Масштабирует пути SVG."""
        return [path.scaled(scale_factor) for path in paths]

    def send_gcode_to_arduino(self):
        ARDUINO_PORT = "COM5"
        BAUD_RATE = 115200

        try:
            self.stop_flag = False  # Сброс флага перед началом отправки
            with serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2) as ser:
                ser.write("?".encode())
                for line in self.gcode:
                    if self.stop_flag:  # Проверяем флаг для остановки
                        print("Transmission stopped by user.")
                        break

                    ser.write(f"{line}\n".encode())
                    response = ser.readline().decode().strip()
                    while response != "ok":
                        if (self.gcode[0] == line): break
                        response = ser.readline().decode().strip()

                    print(f"Sent: {line}. Received: {response}")

                    if "error" in response:
                        print(f"Error detected in G-code: {line}. Stopping transmission.\n")
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
