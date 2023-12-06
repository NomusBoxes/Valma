from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import Update
import random
import os
import asyncio

# Токен, который вы получили от BotFather
TOKEN = '6084387315:AAFUwtNCnFen6x27zkCnWjJeVMc48AFlGZc'

# Путь к папке с видеофайлами
VIDEO_FOLDER_PATH = 'C:/videos'

CODE_WORD = 'lets go'  # Замените на ваше кодовое слово

async def broadcast_video(context):
    try:
        if len(video_archive) > 0:
            video_to_send = video_archive[0]
            with open('user_data.txt', 'r') as file:
                for line in file:
                    user_id, _ = line.strip().split(',')
                    try:
                        with open(video_to_send, 'rb') as video:
                            await context.bot.send_video(chat_id=int(user_id), video=video)
                    except Exception as e:
                        print(f"Failed to send video to {user_id}: {e}")
        else:
            print("No videos in archive.")
    except FileNotFoundError:
        print("No users data found.")



# Создание списка видеофайлов
video_archive = [os.path.join(VIDEO_FOLDER_PATH, f) for f in os.listdir(VIDEO_FOLDER_PATH) if f.endswith('.mp4')]

async def get_last_video_index(user_id):
    try:
        with open('user_data.txt', 'r') as file:
            for line in file:
                user, index = line.strip().split(',')
                if int(user) == user_id:
                    return int(index)
    except FileNotFoundError:
        with open('user_data.txt', 'w') as file:
            pass
    return None

async def update_video_index(user_id, new_index):
    lines = []
    updated = False
    try:
        with open('user_data.txt', 'r') as file:
            for line in file:
                user, index = line.strip().split(',')
                if int(user) == user_id:
                    lines.append(f"{user_id},{new_index}\n")
                    updated = True
                else:
                    lines.append(line)
    except FileNotFoundError:
        pass

    if not updated:
        lines.append(f"{user_id},{new_index}\n")

    with open('user_data.txt', 'w') as file:
        file.writelines(lines)

async def handle_text(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    

    if text.strip().lower() == CODE_WORD.lower():
        await broadcast_video(context)
    else:
        random_responses = ["Не уж то у нас не получилось?(", "Отправь видео, пожалуйста... или фоточку", "Жизнь тлен...", "Будущее ужасно", "Я как-то раз так напился, что пукнул на весь торговый зал и уснул...", "Я люблю тебя, что бы ни случилось...", "Я такой дурак..."]
        response = random.choice(random_responses)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

async def handle_media(update: Update, context):
    user_id = update.effective_user.id
    last_index = await get_last_video_index(user_id)
    if last_index is None or last_index >= len(video_archive) - 1:
        next_index = 0
    else:
        next_index = last_index + 1

    video_to_send = video_archive[next_index]
    with open(video_to_send, 'rb') as video:
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video)
    await update_video_index(user_id, next_index)

async def start(update: Update, context):
    user_id = update.effective_user.id
    if len(video_archive) > 0:
        video_to_send = video_archive[0]
        with open(video_to_send, 'rb') as video:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=video)
        await update_video_index(user_id, 0)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет доступных видео.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

    # Запуск бота
    application.run_polling()
