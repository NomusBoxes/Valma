import random

from nltk.tokenize import word_tokenize


def generate_video_ideas(topic, popular_videos, audience_characteristics, related_information):
    video_ideas = []

    # Генерация идей на основе популярных тем и ключевых слов из заголовков и описаний видео
    for video in popular_videos:
        title_words = word_tokenize(video["title"])
        description_words = word_tokenize(video["description"])
        common_words = set(title_words).intersection(description_words)
        idea = f"Идея для видео: \"{topic} {video['title']}\""
        video_ideas.append(idea)

    # Генерация случайной идеи на основе ключевых слов
    all_words = [word for video in popular_videos for word in
                 set(word_tokenize(video["title"])).intersection(word_tokenize(video["description"]))]
    random.shuffle(all_words)
    random_idea_words = random.sample(all_words, min(7, len(all_words)))
    idea = f"Случайная идея для видео: \"{topic} {' '.join(random_idea_words)}\""
    video_ideas.append(idea)

    # Генерация идей на основе характеристик аудитории
    idea = f"Видео на {audience_characteristics['language']} языке: \"{topic}\""
    video_ideas.append(idea)

    sentiment = audience_characteristics["sentiment"]
    if sentiment != "Нейтральный":
        idea = f"Видео с {sentiment.lower()} настроением: \"{topic}\""
        video_ideas.append(idea)

    common_interests = audience_characteristics["common_interests"]
    if common_interests:
        random_interests = random.sample(common_interests, min(5, len(common_interests)))
        idea = f"Идея на основе интересов аудитории: \"{topic} {', '.join(random_interests)}\""
        video_ideas.append(idea)

    # Генерация идей на основе связанных данных из интернета
    for item in related_information:
        idea = f"Связанная информация: \"{item['title']}\" ({item['link']})"
        video_ideas.append(idea)

    return video_ideas
