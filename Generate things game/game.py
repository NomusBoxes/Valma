import pygame
import pygame_gui
from pygame.locals import *
import requests
import io
from PIL import Image
import threading
import queue
import importlib

import objGenerator

pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('2 Player Game')

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Устанавливаем менеджер для интерфейса
manager = pygame_gui.UIManager((WIDTH, HEIGHT))


class Player:
    def __init__(self, x, y, color, controls):
        self.x = x
        self.y = y
        self.color = color
        self.controls = controls
        self.size = 50
        self.speed = 5

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls["left"]]:
            self.x -= self.speed
        if keys[self.controls["right"]]:
            self.x += self.speed
        if keys[self.controls["up"]]:
            self.y -= self.speed
        if keys[self.controls["down"]]:
            self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

player1 = Player(100, HEIGHT // 2, RED, {"left": K_a, "right": K_d, "up": K_w, "down": K_s})
player2 = Player(WIDTH - 200, HEIGHT // 2, BLUE, {"left": K_LEFT, "right": K_RIGHT, "up": K_UP, "down": K_DOWN})

input_box1 = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((10, 10), (150, 30)), manager=manager)
input_box2 = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((WIDTH - 160, 10), (150, 30)), manager=manager)

# Очередь для изображений, полученных из API
obj_queue = queue.Queue()

created_objects = []

# gen = objGenerator.Generator()
# gen.createObj()


running = True
while running:
    time_delta = pygame.time.Clock().tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        
        # Обработка событий интерфейса
        manager.process_events(event)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL]:
            threading.Thread(target=objGenerator.request_image, args=(input_box1.get_text(), (player1.x, player1.y))).start()
            input_box1.set_text("")
        if keys[pygame.K_RCTRL]:
            threading.Thread(target=objGenerator.request_image, args=(input_box2.get_text(), (player2.x, player2.y))).start()
            input_box2.set_text("")

    screen.fill(WHITE)

    # Отображение изображений из очереди
    for img in created_objects:
        image, position = img
        screen.blit(image, position)

    player1.move()
    player1.draw(screen)
    player2.move()
    player2.draw(screen)

    manager.update(time_delta)
    manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()