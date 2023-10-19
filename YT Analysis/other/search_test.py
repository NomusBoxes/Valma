import requests

# Замените "YOUR_API_KEY" на ваш API-ключ
API_KEY = "AIzaSyCVhkz39Yp4hg6N91dLEeh97kelumPVkj8"

def search_google(query, num_results=10):
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": "0446b10286f24479f",  # Это пример cx, но он игнорируется при использовании API-ключа
        "q": query,
        "num": num_results
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if "items" in data:
        return [item["title"] for item in data["items"]]
    else:
        return []

# Пример использования функции search_google
query = "Python programming"
results = search_google(query)

print("Результаты поиска для запроса:", query)
for i, result in enumerate(results, start=1):
    print(f"{i}. {result}")
