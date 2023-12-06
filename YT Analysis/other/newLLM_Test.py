import requests
import tkinter as tk
from tkinter import ttk
import googleapiclient.discovery
import googleapiclient.errors
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from langdetect import detect
from textblob import TextBlob
import pymorphy2


# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

cache = {}

# Function to analyze text and extract keywords
def analyze_text(text):
    stop_words = set(stopwords.words("russian"))
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalpha() and word not in stop_words]
    return words


# Function to analyze audience comments and generate video ideas
def analyze_audience_comments(api_key, video_ids):
    all_comments = []
    for video_id in video_ids:
        comments = get_video_comments(api_key, video_id)
        if comments:
            all_comments.extend(comments)

    audience_characteristics = {}

    lang = detect(" ".join(all_comments))
    audience_characteristics["language"] = lang

    blob = TextBlob(" ".join(all_comments))
    sentiment_polarity = blob.sentiment.polarity
    if sentiment_polarity > 0:
        audience_characteristics["sentiment"] = "Positive"
    elif sentiment_polarity < 0:
        audience_characteristics["sentiment"] = "Negative"
    else:
        audience_characteristics["sentiment"] = "Neutral"

    stop_words = set(stopwords.words("russian"))
    words = word_tokenize(" ".join(all_comments).lower())
    words = [word for word in words if word.isalpha() and word not in stop_words]

    morph = pymorphy2.MorphAnalyzer()
    lemmas = [morph.parse(word)[0].normal_form for word in words]
    word_freq = Counter(lemmas)
    corpus = [[(word_id, word_count) for word_id, word_count in word_freq.items()]]
    try:
        lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus, num_topics=3,
                                                    id2word=gensim.corpora.Dictionary([lemmas]), passes=10)
        topics = lda_model.print_topics(num_words=3)
        common_topics = [topic[1] for topic in topics]
        audience_characteristics["interests"] = common_topics
    except Exception as e:
        print("An error occurred while analyzing audience comments:", e)
        audience_characteristics["interests"] = []

    return audience_characteristics


# Function to generate video ideas based on topic modeling
def generate_video_ideas(topic, popular_videos, audience_characteristics, related_information):
    ideas = []
    for video in popular_videos:
        ideas.append("Top viewed video: '{}'".format(video["title"]))

    if audience_characteristics:
        lang = audience_characteristics.get("language")
        if lang:
            ideas.append("Audience language: {}".format(lang))

        sentiment = audience_characteristics.get("sentiment")
        if sentiment:
            ideas.append("Audience sentiment: {}".format(sentiment))

        interests = audience_characteristics.get("interests")
        if interests:
            ideas.append("Audience interests:")
            for interest in interests:
                ideas.append("- {}".format(interest))

    if related_information:
        ideas.append("Related information:")
        for item in related_information:
            ideas.append("- {}".format(item["title"]))

    return ideas


# Function to get data from YouTube API
def get_popular_videos(api_key, topic):
    if topic in cache:
        return cache[topic]

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "part": "snippet",
        "q": topic,
        "type": "video",
        "order": "viewCount",
        "maxResults": 5
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        videos = data.get("items", [])
        result = [{"video_id": video["id"]["videoId"], "title": video["snippet"]["title"]} for video in videos]
        cache[topic] = result
        return result
    else:
        print("An error occurred:", response.status_code)


# Function to search related information through Google API
def search_related_information(api_key, query):
    if query in cache:
        return cache[query]

    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": "0446b10286f24479f",
        "q": query,
        "num": 5
    }

    response = requests.get(base_url, params=params)

    data = response.json()
    if "items" in data:
        related_information = data["items"]
        cache[query] = related_information
        return related_information


# Function to get video comments from YouTube API
def get_video_comments(api_key, video_id):
    if video_id in cache:
        return cache[video_id]

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

        cache[video_id] = comments
        return comments

    except googleapiclient.errors.HttpError as e:
        print("An error occurred:", e)
        return None


# Main function to generate ideas from GUI
def generate_ideas_from_gui():
    def on_generate_ideas_button_click():
        api_key = "AIzaSyCE0PKf-X0cVq43J21cmTCplNQdCS9ntYs"  # Replace with your API key
        topic = topic_entry.get()
        topic_keywords = analyze_text(topic)
        popular_videos = get_popular_videos(api_key, topic)

        audience_characteristics = None
        related_information = None

        audience_characteristics = analyze_audience_comments(api_key, [video["video_id"] for video in popular_videos])
        related_information = search_related_information(api_key, topic)

        video_ideas = generate_video_ideas(topic, popular_videos, audience_characteristics, related_information)

        results_text.delete(1.0, tk.END)

        results_text.insert(tk.END, "Video ideas for the topic '{}'\n".format(topic))
        for i, idea in enumerate(video_ideas, 1):
            results_text.insert(tk.END, "{}. {}\n".format(i, idea))

    root = tk.Tk()
    root.title("Video Idea Generator")
    root.geometry("1024x720")

    topic_label = ttk.Label(root, text="Topic for video:")
    topic_label.pack(pady=10)

    topic_entry = ttk.Entry(root)
    topic_entry.pack(pady=5)

    generate_ideas_button = ttk.Button(root, text="Generate Ideas", command=on_generate_ideas_button_click)
    generate_ideas_button.pack(pady=10)

    results_text = tk.Text(root, wrap=tk.WORD, font=("Helvetica", 12))
    results_text.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    generate_ideas_from_gui()
