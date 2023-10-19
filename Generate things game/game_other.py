import pygame
from pygame.locals import *
import requests
from io import BytesIO
import io
from PIL import Image
import pygame_gui

# Настройки Pygame
pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('2 Player Game')

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# API Hugging Face
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
headers = {"Authorization": "Bearer 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"}


def get_image_from_huggingface(description):
    payload = {"inputs": description}
    response = requests.post(API_URL, headers=headers, json=payload)
    image_data = response.content
    return Image.open(io.BytesIO(image_data))

# Класс для игрока
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

# Создание игроков
player1 = Player(100, HEIGHT//2, RED, {"left": K_a, "right": K_d, "up": K_w, "down": K_s})
player2 = Player(WIDTH-200, HEIGHT//2, BLUE, {"left": K_LEFT, "right": K_RIGHT, "up": K_UP, "down": K_DOWN})

# Получение изображения
description = "Astronaut riding a horse"
image_pil = get_image_from_huggingface(description)

# Преобразование изображения PIL в Pygame Surface
image_io = BytesIO()
image_pil.save(image_io, format="PNG")
image_io.seek(0)
pygame_image = pygame.image.load(image_io)

# Изменение размера изображения до 20x20 пикселей
pygame_image = pygame.transform.scale(pygame_image, (20, 20))

# Основной игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    screen.fill(WHITE)
    
    # Отображение изображения в игре
    screen.blit(pygame_image, (WIDTH//2 - 10, HEIGHT//2 - 10))  # Центр экрана, например

    player1.move()
    player1.draw(screen)
    player2.move()
    player2.draw(screen)

    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()
