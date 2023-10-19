import requests
import pygame
from pygame.locals import *
import requests
import io
from PIL import Image
import queue

# API Llama 2
API_URL_Llama = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-hf"
headers = {"Authorization": "Bearer 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"}


# API Hugging Face
API_URL_HF = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
headers = {"Authorization": "Bearer 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"}

class Generator:
    def createObj(self, obj_name, obj_pos):
        result = self.generateBehaviour(obj_name)
        code = result.get("generated_code", "")  
        self.save_behaviour_to_file(obj_name, code)




    def generateBehaviour(obj_name):    
        with open("game.py", 'r') as mainGame:
            response = requests.post(API_URL_Llama, headers=headers, json={"inputs": "I have this game where players must defeat each other with everything they" +
                                                                    "have in mind. Here is the base code: " + str(mainGame) 
                                                                    +"\n You will generate behaviour for new things. No decription of the code, please. Only raw code."+
                                                                    "Now player created: " + obj_name + ". Generate some of the characterictics of the object and" +
                                                                    + "implement them by creating new py file with its behaviour"})
            return response.json()
    
    def get_image_from_huggingface(self, description):
        payload = {"inputs": description}
        response = requests.post(API_URL_HF, headers=headers, json=payload)
        return Image.open(io.BytesIO(response.content))

    def request_image(self, description, position):
        print('Sent request')
        image_pil = self.get_image_from_huggingface(description)
        image_io = io.BytesIO()
        image_pil.save(image_io, format="PNG")
        image_io.seek(0)
        pygame_image = pygame.image.load(image_io).convert_alpha()
        pygame_image = pygame.transform.scale(pygame_image, (50, 50))
        return pygame_image
        #image_queue.put((pygame_image, position))
        #drawn_images.append((pygame_image, position))

    def save_behaviour_to_file(self, obj_name, code):
        with open(f"{obj_name}_behaviour.py", "w") as f:
            f.write(code)


    

