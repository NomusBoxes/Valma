import tkinter as tk
from tkinter import filedialog, Text
from svgpathtools import svg2paths
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
from serial.tools import list_ports

from image_utils import *

import shutil
import os
import threading
from PIL import Image
from image_utils import get_image_from_huggingface
import time
from tkinter import ttk
import math
import tkinter.messagebox as messagebox



MACHINE_MAX_X = 60
MACHINE_MAX_Y = 60


class GCodeVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Да будет торт!")
        #self.geometry("+800+350")
        
        self.port_label = ttk.Label(self, text="Порт:")
        self.port_label.pack()

        self.ports_combobox = ttk.Combobox(self, values=[port.device for port in list_ports.comports()], width=15)
        self.ports_combobox.pack(pady=20)

        self.load_button = tk.Button(self, text="Открыть", command=self.load_image, width=15)
        self.load_button.pack(pady=20)
        

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = None

    
        self.raduis_label = ttk.Label(self, text="Радиус")
        self.raduis_label.pack()
        self.radius = ttk.Entry(self)
        self.radius.pack(pady=20)

        self.send_gcode_button = tk.Button(self, text="Установить радиус", command=self.setRadius, width=15)
        self.send_gcode_button.pack(pady=20, padx=20)

        self.send_gcode_button = tk.Button(self, text="Начать печать", command=self.start_send_gcode_thread, width=15)
        self.send_gcode_button["state"] = "disabled"
        self.send_gcode_button.pack(pady=20, padx=20)

        self.stop_gcode_button = tk.Button(self, text="Сброс и ресет", command=self.stop_and_reset, width=15)
        self.stop_gcode_button["state"] = "disabled"
        self.stop_gcode_button.pack(pady=20, padx=20)

        self.pause_label = ttk.Label(self, text="Пауза")
        self.pause_label.pack()
        self.pause = ttk.Entry(self)
        self.pause.configure(textvariable="1")
        self.pause.pack(pady=20)

        self.force_label = ttk.Label(self, text="Подача")
        self.force_label.pack()
        self.force = ttk.Entry(self)
        self.force.configure(textvariable="1000")
        self.force.pack(pady=20)
        # grbl_port = self.detect_grbl_port()
        # if grbl_port:
        #     self.ports_combobox.set(grbl_port)
        # else:
        #     print("GRBL device not found!")

        self.gcode = []
        self.paths = []
        self.inverted = False
        self.stop_flag = False  # Флаг для остановки отправки кода
    
    def setRadius(self):
        global MACHINE_MAX_X
        global MACHINE_MAX_Y
        MACHINE_MAX_X = float(self.radius.get())/2
        MACHINE_MAX_Y = float(self.radius.get())/2
        # Масштабирование путей SVG
                

        x_min, x_max, y_min, y_max = get_svg_bounds(self.paths)
        svg_width = x_max - x_min
        svg_height = y_max - y_min

        # Вычисляем коэффициент масштабирования
        scale_factor = min(MACHINE_MAX_X / svg_width, MACHINE_MAX_Y / svg_height)

        # Если коэффициент масштабирования больше 1, устанавливаем его равным 1,
        # чтобы изображение не увеличивалось больше своего исходного размера.

        self.paths = self.scale_paths(self.paths, scale_factor)

        # Генерация G-code с учетом масштабированных путей
        self.generate_gcode()

        # Визуализация G-code
        self.visualize_gcode()

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
                scale_factor = min(MACHINE_MAX_X / (svg_width), MACHINE_MAX_Y / (svg_height))

                # Если коэффициент масштабирования больше 1, устанавливаем его равным 1,
                # чтобы изображение не увеличивалось больше своего исходного размера.

                self.paths = self.scale_paths(self.paths, scale_factor)

                # Генерация G-code с учетом масштабированных путей
                self.generate_gcode()

                # Визуализация G-code
                self.visualize_gcode()

                shutil.rmtree(temp_folder)
                self.send_gcode_button["state"] = "active"
                
            except Exception as e:
                print(f"Error: {e}")
                # Здесь, вы можете отобразить всплывающее сообщение об ошибке пользователю, используя messagebox в tkinter.

    def calculate_feedrate(self, prev_point, current_point, max_distance, max_feedrate):
        distance = math.sqrt((prev_point[0] - current_point[0]) ** 2 + (prev_point[1] - current_point[1]) ** 2)
        if distance == 0:
            return max_feedrate
        return min(max_feedrate, max_feedrate * max_distance / max(distance, 1))  # Предотвращаем деление на ноль


    def generate_gcode(self):
        max_distance = 30
        max_feedrate = 1000


        self.gcode = ["G90"]
        x_center = MACHINE_MAX_X / 2
        y_center = MACHINE_MAX_Y / 2
        radius = MACHINE_MAX_X / 2

        # Генерация круглого контура с помощью маленьких отрезков
        N = 100
        angle_step = 2 * math.pi / N

        # Начальная точка
        x_start = x_center + radius * math.cos(0)
        y_start = y_center + radius * math.sin(0)
        self.gcode.append(f"G0 X{x_start:.2f} Y{y_start:.2f} F1000")  # Перемещение к начальной точке
        self.gcode.append("M03S25")  # Опускание пера
        prev_point = [x_center, y_center]

        for i in range(1, N + 1):
            angle = i * angle_step
            x = x_center + radius * math.cos(angle)
            y = y_center + radius * math.sin(angle)
            self.gcode.append(f"G01 X{x:.2f} Y{y:.2f} F1000")

        self.gcode.append("M03S35")  # Поднятие пера

        # Масштабирование и центрирование изображения SVG
        MARGIN = 5 * MACHINE_MAX_X/50
        x_min, x_max, y_min, y_max = get_svg_bounds(self.paths)
        svg_width = x_max - x_min
        svg_height = y_max - y_min
        image_diameter = 2 * radius - 2 * MARGIN

        # Вычисляем коэффициент масштабирования
        scale_factor = image_diameter / max(svg_width, svg_height)

        self.paths = self.scale_paths(self.paths, scale_factor)

        # Вычислите смещение для центрирования
        x_offset = x_center - (x_min + svg_width / 2) * scale_factor
        y_offset = y_center - (y_min + svg_height / 2) * scale_factor
        self.paths = [path.translated(complex(x_offset, y_offset)) for path in self.paths]

        # Генерация G-code для изображения
        for path in self.paths:
            if path:
                start_x, start_y = path.start.real, path.start.imag
                feedrate = self.calculate_feedrate(prev_point, [start_x, start_y], max_distance, max_feedrate)
                self.gcode.append(f"G01 X{start_x:.2f} Y{start_y:.2f} F{feedrate}")

                # 3. Drop the pen down
                self.gcode.append("M03S25")
                self.gcode.append(f"M100")

                for segment in path:
                    # 4. Move through the path
                    x, y = segment.end.real, segment.end.imag
                    if self.inverted:
                        y = -y
                    feedrate = self.calculate_feedrate([segment.start.real, segment.start.imag], [x, y], max_distance, max_feedrate)
                    self.gcode.append(f"G01 X{x:.2f} Y{y:.2f} F{feedrate}")
                    
                    # 5. Lift the pen at the end of the path
                    self.gcode.append(f"M101")
                    self.gcode.append("M03S35")

            prev_point = [segment.end.real, segment.end.imag]  # Обновляем предыдущую точку

        self.gcode.append("G01 X0 Y0")

    def detect_grbl_port(self):
        available_ports = [port.device for port in list_ports.comports()]
        for port in available_ports:
            try:
                with serial.Serial(port, 115200, timeout=5) as ser:  # Увеличено время ожидания
                    time.sleep(1)  # Даем время на инициализацию
                    ser.flushInput()  # Очищаем буфер от возможных предыдущих данных
                    ser.write("?".encode())
                    time.sleep(0.5)  # Пауза перед попыткой чтения
                    response = ser.readline().decode().strip()
                    if "Grbl" in response:
                        return port
            except:
                pass  # Просто переходим к следующему порту
        return None  # Если GRBL порт не найден



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
            elif "M03S35" in point:  # Split segments only on pen up command
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
       # self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def scale_paths(self, paths, scale_factor):
        """Масштабирует пути SVG."""
        return [path.scaled(scale_factor) for path in paths]

    def send_gcode_to_arduino(self):
        ARDUINO_PORT = self.ports_combobox.get()
        BAUD_RATE = 115200

        # Отправляем только контур круга
        contour_gcode = self.generate_contour_gcode()  # Новая функция для генерации G-code контура
        self.send_specific_gcode(contour_gcode, ARDUINO_PORT, BAUD_RATE)

    

        # Отображаем диалоговое окно
        answer = messagebox.askyesno("Подтверждение",
                                     "Поместите торт внутрь контура. Продолжить?")
        
        if answer:  # Если пользователь нажал "продолжить"
            # Отправляем оставшийся G-code
            image_gcode = self.gcode[len(contour_gcode):]  # Все команды G-code, кроме контура
            image_gcode.insert(2, "M03S25M100")
            self.send_specific_gcode(image_gcode, ARDUINO_PORT, BAUD_RATE)

    def generate_contour_gcode(self):
        # Функция генерации G-code только для контура круга
        # Это по сути та часть, которая создает круг в функции generate_gcode
        gcode = ["?"]
        gcode.append("M03S35")
        x_center = MACHINE_MAX_X / 2
        y_center = MACHINE_MAX_Y / 2
        radius = MACHINE_MAX_X / 2

        N = 100
        angle_step = 2 * math.pi / N

        x_start = x_center + radius * math.cos(0)
        y_start = y_center + radius * math.sin(0)
        gcode.append(f"G0 X{x_start:.2f} Y{y_start:.2f}")  
        gcode.append("M03S25")  
        gcode.append(f"G01 X{x_start:.2f} Y{y_start:.2f} F1000")
        gcode.append("M03S25")
        for i in range(2, N + 1):
            angle = i * angle_step
            x = x_center + radius * math.cos(angle)
            y = y_center + radius * math.sin(angle)
            gcode.append(f"G01 X{x:.2f} Y{y:.2f} F1000")

         
        gcode.append("M03S35")
        gcode.append("G01X0Y0")   
        return gcode

    def send_specific_gcode(self, gcode, port, baud_rate):
        # Отправка указанного списка G-code
        try:
            self.stop_gcode_button["state"] = "active"
            self.stop_flag = False
            with serial.Serial(port, baud_rate, timeout=2) as ser:
                ser.write("?".encode())
                for line in gcode:
                    if self.stop_flag:
                        time.sleep(3)  # даем время на завершение текущей операции
                        ser.write("M03S35\n".encode())  # поднимаем шпиндель
                        time.sleep(0.5)
                        ser.write("G0X0Y0 F1000\n".encode())  # двигаемся в начальную позицию
                        print("Transmission stopped by user.")
                        self.stop_flag = False
                        return  # завершаем выполнение функции
                    # if "F1000" in line:
                    #     line = line.replace("F1000", f"F{int(self.force.get())}")
                    ser.write(f"{line}\n".encode())
                    if "M100" in line:
                        print("####M100 in line####")
                        time.sleep(float(self.pause.get()))  # добавляем задержку в 2 секунды после команды M100
                    time.sleep(0.05)  # добавим небольшую задержку перед чтением ответа
                    response = ser.readline().decode().strip()

                    while not response:  # ждем ответа от Ардуино
                        response = ser.readline().decode().strip()
                    
                    print(f"Sent: {line}. Received: {response}")

                    if "error" in response:
                        print(f"Error detected in G-code: {line}. Stopping transmission.\n")
                        break

        except Exception as e:
            print(f"Error: {e}")

            
    def update_scale(self, scale_value):
    # Генерация G-code с учетом нового масштаба
        self.generate_gcode()

        # Визуализация обновленного G-code
        self.visualize_gcode()

    def run(self):
        self.root.mainloop()
