import requests
from googleapiclient.discovery import build
import tkinter as tk
from tkinter import ttk
import googleapiclient.discovery
import googleapiclient.errors
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from langdetect import detect
from textblob import TextBlob  # Добавляем этот импорт

# Загрузка данных для nltk
nltk.download('punkt')
nltk.download('stopwords')

MAX_VIDEOS = 10
MAX_SEARCH_RESULTS = 10

# Функция для анализа текста и получения ключевых слов
def analyze_text(text):
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalpha() and word not in stop_words]
    return words


# Функция для получения данных из YouTube API
def get_popular_videos(api_key, topic):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "part": "snippet",
        "q": topic,
        "type": "video",
        "order": "viewCount",
        "maxResults": MAX_VIDEOS
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        videos = data.get("items", [])
        return [{"video_id": video["id"]["videoId"], "title": video["snippet"]["title"]} for video in videos]
    else:
        print("An error occurred:", response.status_code)


# Функция для поиска связанной информации через Google API
def search_related_information(api_key, query):
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": "0446b10286f24479f",  # Это пример cx, но он игнорируется при использовании API-ключа
        "q": query,
        "num": MAX_SEARCH_RESULTS
    }

    response = requests.get(base_url, params=params)

    data = response.json()
    if "items" in data:
        related_information = data["items"]
        return related_information


# Функция для генерации идей для видео
def generate_video_ideas(topic, popular_videos, audience_characteristics, related_information):
    ideas = []
    for video in popular_videos:
        ideas.append("Топ просматриваемого видео: '{}'".format(video["title"]))

    if audience_characteristics:
        lang = audience_characteristics.get("language")
        if lang:
            ideas.append("Язык аудитории: {}".format(lang))

        age_group = audience_characteristics.get("age_group")
        if age_group:
            ideas.append("Возрастная группа аудитории: {}".format(age_group))

        gender = audience_characteristics.get("gender")
        if gender:
            ideas.append("Пол аудитории: {}".format(gender))

    if related_information:
        ideas.append("Связанная информация:")
        for item in related_information:
            ideas.append(item["title"])

    return ideas


# Функция для анализа комментариев и определения характеристик аудитории с использованием langdetect
def get_video_comments(api_key, video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        )
        response = request.execute()

        comments = []
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)

        return comments

    except googleapiclient.errors.HttpError as e:
        print("An error occurred:", e)
        return None


def analyze_audience_comments(api_key, video_ids):
    all_comments = []
    for video_id in video_ids:
        comments = get_video_comments(api_key, video_id)
        if comments:
            all_comments.extend(comments)

    audience_characteristics = {}

    # Определение языка комментариев
    audience_characteristics["language"] = detect(" ".join(all_comments))

    # Определение настроения и сентимента комментариев
    blob = TextBlob(" ".join(all_comments))
    sentiment_polarity = blob.sentiment.polarity
    if sentiment_polarity > 0:
        audience_characteristics["sentiment"] = "Позитивный"
    elif sentiment_polarity < 0:
        audience_characteristics["sentiment"] = "Негативный"
    else:
        audience_characteristics["sentiment"] = "Нейтральный"

    # Определение ключевых интересов аудитории на основе частоты слов
    common_words = [word for word, count in blob.word_counts.items() if count >= 10]
    audience_characteristics["common_interests"] = common_words

    return audience_characteristics


# Основная функция для анализа текста и получения идей для видео
def generate_ideas_from_gui():
    def on_generate_ideas_button_click():
        api_key = "AIzaSyCVhkz39Yp4hg6N91dLEeh97kelumPVkj8"  # Замените на ваш ключ API
        topic = topic_entry.get()
        topic_keywords = analyze_text(topic)
        popular_videos = get_popular_videos(api_key, topic)

        audience_characteristics = None
        related_information = None

        # if popular_videos:
        audience_characteristics = analyze_audience_comments(api_key, [video["video_id"] for video in popular_videos])
        related_information = search_related_information(api_key, topic)

        video_ideas = generate_video_ideas(topic, popular_videos, audience_characteristics, related_information)

        # Очищаем текущие результаты
        results_text.delete(1.0, tk.END)

        # Выводим идеи для видео
        results_text.insert(tk.END, "Идеи для видео по теме '{}'\n".format(topic))
        # for idea in video_ideas:
        #    results_text.insert(tk.END, "{}\n".format(idea))

        for i, idea in enumerate(video_ideas, 1):
            results_text.insert(tk.END, "{}. {}\n".format(i, idea))

    # Создаем графический интерфейс
    root = tk.Tk()
    root.title("Генератор идей для видео")
    root.geometry("1024x720")

    # Создаем виджеты
    topic_label = ttk.Label(root, text="Тема для видео:")
    topic_label.pack(pady=10)

    topic_entry = ttk.Entry(root)
    topic_entry.pack(pady=5)

    generate_ideas_button = ttk.Button(root, text="Сгенерировать идеи", command=on_generate_ideas_button_click)
    generate_ideas_button.pack(pady=10)

    results_text = tk.Text(root, wrap=tk.WORD, font=("Helvetica", 12))
    results_text.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    generate_ideas_from_gui()
