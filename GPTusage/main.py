import openai

openai.api_key = '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'

# Чтение данных из файла с указанием кодировки UTF-8
with open('data.txt', 'r', encoding='utf-8') as file:
    data = file.read()

# Разбиение данных на записи
video_records = data.split("Video title:")

# Заполнение промпта данными из файла и шаблона
prompt_template = f"""
Generate me video ideas on topic '{{topic}}' using the following information:
{{data}}

User: {{user_input}}
AI:
"""

# Запрос ввода темы
user_input = input("User: Введите тему для видео: ")


# Объединение всех записей в одну строку
all_records = '\n'.join(video_records)

# Разбиваем все данные на более мелкие части
chunks = [all_records[i:i + 3000] for i in range(0, len(all_records), 3000)]

ai_responses = []

response = openai.Completion.create(
        engine="text-davinci-003",
        prompt="I'l provide you information about videos by parts, because of token limitations. Tell me just 'saved...' when you recieve the part. When I say 'thats all' wait for another prompt but using info as context",
        max_tokens=1024
    )

for chunk in chunks:
    # Заполнение шаблона промпта данными
    prompt = f"Here is the part: {chunk}"

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1024
    )

    ai_responses.append(response.choices[0].text.strip())

response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"thats all. Generate me video ideas on topic {user_input} using the recieved data:",
        max_tokens=1024
    )
    

    


