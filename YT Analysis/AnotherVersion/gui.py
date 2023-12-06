import tkinter as tk
from tkinter import scrolledtext
from youtube_api import get_popular_videos
from text_analysis import analyze_text, analyze_audience_comments
from google_search_api import search_related_information
from video_ideas import generate_video_ideas
from text_analysis import get_all_comments

comments_are_shown = False


def show_comments(event):
    global comments_are_shown

    # Получаем индекс выбранного элемента списка
    index = result_listbox.curselection()
    if not index:
        return

    # Получаем данные о выбранном видео
    selected_video_index = int(index[0])
    selected_video = popular_videos[selected_video_index]

    # Удаляем старые комментарии текущего видео из списка
    selected_video_comments = selected_video.get("comments", [])

    if comments_are_shown:
        if selected_video_comments:
            result_listbox.delete(selected_video_index + 1, selected_video_index + 3)
        comments_are_shown = False
    else:
        comments = selected_video_comments or get_all_comments(api_key, selected_video["video_id"])
        selected_video["comments"] = comments
        sorted_comments = sorted(comments, key=lambda x: x["snippet"]["topLevelComment"]["snippet"]["likeCount"],
                                 reverse=True)[:3]
        # Выводим комментарии в список с отступом в виде пробелов
        for comment in sorted_comments:
            result_listbox.insert(selected_video_index + 1,
                                  f"             {comment['snippet']['topLevelComment']['snippet']['textOriginal']}")
        comments_are_shown = True


# Функция для обновления списка идей
def update_ideas():
    topic = topic_entry.get()
    global popular_videos
    popular_videos = get_popular_videos(api_key, topic)
    if not popular_videos:
        result_listbox.delete(0, tk.END)
        result_listbox.insert(tk.END, "Не удалось найти популярные видео по заданной теме.")
        return

    # Очищаем список перед обновлением
    result_listbox.delete(0, tk.END)

    all_titles = [video["title"] for video in popular_videos]
    all_descriptions = [video["description"] for video in popular_videos]
    all_tags = [tag for video in popular_videos for tag in video.get("tags", [])]

    title_word_freq = analyze_text(all_titles)
    description_word_freq = analyze_text(all_descriptions)
    tag_word_freq = analyze_text(all_tags)

    audience_characteristics = analyze_audience_comments(api_key, [video["video_id"] for video in popular_videos])

    related_information = search_related_information(api_key, topic)

    video_ideas = generate_video_ideas(topic, popular_videos, audience_characteristics, related_information)

    # Выводим идеи в список
    for i, idea in enumerate(video_ideas, 1):
        result_listbox.insert(tk.END, f"{i}. {idea}")


# Создаем графический интерфейс
root = tk.Tk()
root.title("YouTube Idea Generator")
root.geometry("800x600")

api_key = "AIzaSyCVhkz39Yp4hg6N91dLEeh97kelumPVkj8"

label = tk.Label(root, text="Введите тему для генерации идей:")
label.pack(pady=10)

topic_entry = tk.Entry(root, width=50)
topic_entry.pack()

button = tk.Button(root, text="Генерировать идеи", command=update_ideas)
button.pack(pady=10)

# Создаем список для вывода идей
result_listbox = tk.Listbox(root, width=120, height=30)
result_listbox.pack()

# Добавляем обработчик события для клика на элемент списка
result_listbox.bind("<ButtonRelease-1>", show_comments)

root.mainloop()
