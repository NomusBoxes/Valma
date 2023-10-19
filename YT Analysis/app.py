import tkinter as tk
from cgitb import text
from tkinter import scrolledtext
from ideagenerator import generate_idea

comments_are_shown = False

API_KEY = "AIzaSyCVhkz39Yp4hg6N91dLEeh97kelumPVkj8"


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
    video_ideas = []
    for i in range(0, 1):
        video_ideas.append(generate_idea(API_KEY, topic_entry.get()))

    # (generate_video_ideas(topic, popular_videos, audience_characteristics, related_information))

    # Выводим идеи в список
    for i, idea in enumerate(video_ideas, 1):
        # result_listbox.insert(tk.END, f"{i}. {idea}")
        result.config(text=str(idea))


# Создаем графический интерфейс
root = tk.Tk()
root.title("YouTube Idea Generator")
root.geometry("800x600")

label = tk.Label(root, text="Введите тему для генерации идей:")
label.pack(pady=10)

topic_entry = tk.Entry(root, width=50)
topic_entry.pack()

button = tk.Button(root, text="Генерировать идеи", command=update_ideas)
button.pack(pady=10)

result = tk.Label(root, width=120, height=30)
result.pack()
# Создаем список для вывода идей
# result_listbox = tk.Listbox(root, width=120, height=30)
# result_listbox.pack()

# Добавляем обработчик события для клика на элемент списка
#result_listbox.bind("<ButtonRelease-1>", show_comments)

root.mainloop()
