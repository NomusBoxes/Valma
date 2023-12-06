import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from langdetect import detect
from textblob import TextBlob
from youtube_api import get_video_comments
import requests

# Загрузка стоп-слов и пунктуации
nltk.download("punkt")
nltk.download("stopwords")
stop_words = set(stopwords.words("russian"))

stop_words.update(stopwords.words("english"))


# Функция для анализа текста и извлечения ключевых слов
def analyze_text(texts):
    all_text = " ".join(texts)
    words = word_tokenize(all_text.lower())
    words = [word for word in words if word.isalpha() and word not in stop_words]
    word_freq = Counter(words)
    return word_freq


def get_all_comments(api_key, video_id):
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": api_key,
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100
    }

    all_comments = []

    while True:
        response = requests.get(base_url, params=params)
        data = response.json()

        if "items" in data:
            all_comments.extend(data["items"])

        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break

    # Сортировка комментариев по количеству лайков в убывающем порядке
    all_comments.sort(key=lambda x: x["snippet"]["topLevelComment"]["snippet"]["likeCount"], reverse=True)

    # Возвращаем только топ 10 комментариев
    top_10_comments = all_comments[:10]

    return top_10_comments


# Функция для анализа комментариев и определения характеристик аудитории с использованием langdetect
def analyze_audience_comments(api_key, video_ids):
    all_comments = []
    for video_id in video_ids:
        all_comments.extend(get_all_comments(api_key, video_id))

    all_comments_text = [comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for comment in all_comments]
    audience_characteristics = {"language": detect(" ".join(all_comments_text))}

    # Определение настроения и сентимента комментариев
    blob = TextBlob(" ".join(all_comments_text))
    sentiment_polarity = blob.sentiment.polarity
    if sentiment_polarity > 0:
        audience_characteristics["sentiment"] = "Позитивный"
    elif sentiment_polarity < 0:
        audience_characteristics["sentiment"] = "Негативный"
    else:
        audience_characteristics["sentiment"] = "Нейтральный"

    # Определение ключевых интересов аудитории на основе частоты слов
    all_comments_words = [word_tokenize(comment.lower()) for comment in all_comments_text]
    all_comments_words_flat = [word for sublist in all_comments_words for word in sublist]
    interests = set(analyze_text(all_comments_words_flat).items())
    common_words = [word for word, count in interests if count >= 5]

    audience_characteristics["common_interests"] = common_words

    return audience_characteristics
