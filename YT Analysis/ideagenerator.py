import random
import requests
import nltk
from nltk.corpus import stopwords
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from datagrabber import (search_related_information, get_popular_videos, get_video_comments)

import torch

# Установим стоп-слова для NLTK, чтобы удалить их из текста
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# Загружаем предобученную модель GPT-2 и токенизатор
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)


# Функция для сбора данных для генерации идей
def gather_data(api_key, query):
    # Собираем связанные запросы
    related_information = search_related_information(api_key, query)

    # Собираем популярные видео по запросу
    popular_videos = get_popular_videos(api_key, query)

    # Собираем комментарии к популярным видео
    comments = []
    for video in popular_videos:
        video_id = video["video_id"]
        video_comments = get_video_comments(api_key, video_id)
        comments.extend(video_comments)

    return related_information, comments, popular_videos


# Функция для генерации идеи на основе собранных данных
# Функция для генерации идеи на основе собранных данных
# Функция для генерации идеи на основе собранных данных
def generate_idea(api_key, query):
    # Получаем собранные данные
    related_information, comments, popular_videos = gather_data(api_key, query)

    # Объединим данные в один текст
    combined_text = ("Generate me a video idea on topic '" + query
                     + "', if i have this info of title of popular videos, their comments"
                     + " and related information from net: \n")

    for video in popular_videos:
        combined_text += "Video title: \n"
        combined_text += f" {video['title']}\n"
        combined_text += "Описание видео: \n"
        combined_text += f" {video['description']}\n\n"

        combined_text += "\nSearch result: \n"
        for info in related_information:
            combined_text += f"{info['title']}\n"

        combined_text += "\nComments: \n"
        comments = get_video_comments(api_key, video['video_id'])
        for comment in comments:
            combined_text += f"{comment}\n"

    with open('data.txt', 'w', encoding='utf-8') as file:
        file.write(combined_text)

    # Разделим текст на отдельные предложения и токенизируем каждое предложение по отдельности
    sentences = nltk.sent_tokenize(combined_text)
    tokenized_sentences = [tokenizer.encode(sentence, add_special_tokens=False) for sentence in sentences]

    # Объединим токенизированные предложения и ограничим длину общего текста до 1024 токенов
    inputs = []
    for tokens in tokenized_sentences:
        if len(inputs) + len(tokens) <= 1024:
            inputs.extend(tokens)
        else:
            break

    # Преобразуем в формат тензора
    inputs = torch.tensor([inputs])

    # Генерируем идею с помощью модели GPT-2
    with torch.no_grad():
        outputs = model.generate(inputs, max_length=1024, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id)

    idea = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return idea
