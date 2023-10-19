import requests

# Функция для поиска связанных данных в интернете
import requests


def search_related_information(api_key, query):
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": "0446b10286f24479f",  # Это пример cx, но он игнорируется при использовании API-ключа
        "q": query,
        "num": 5
    }

    response = requests.get(base_url, params=params)

    data = response.json()
    if "items" in data:
        related_information = data["items"]
        return related_information

