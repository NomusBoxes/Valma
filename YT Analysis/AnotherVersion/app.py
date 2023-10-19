import random
from flask import Flask, render_template, request

from youtube_api import get_popular_videos
from text_analysis import analyze_text, analyze_audience_comments, get_all_comments
from google_search_api import search_related_information
from video_ideas import generate_video_ideas

app = Flask(__name__)

comments_are_shown = False
popular_videos = []
api_key = "AIzaSyCVhkz39Yp4hg6N91dLEeh97kelumPVkj8"  # Замените на свой ключ API


def show_comments(selected_video_index):
    global comments_are_shown

    selected_video = popular_videos[selected_video_index]

    selected_video_comments = selected_video.get("comments", [])

    if comments_are_shown:
        if selected_video_comments:
            popular_videos[selected_video_index]['comments'] = []
        comments_are_shown = False
    else:
        comments = selected_video_comments or get_all_comments(api_key, selected_video["video_id"])
        popular_videos[selected_video_index]['comments'] = comments
        sorted_comments = sorted(comments, key=lambda x: x["snippet"]["topLevelComment"]["snippet"]["likeCount"],
                                 reverse=True)[:3]
        for comment in sorted_comments:
            popular_videos[selected_video_index]['comments'].append(
                f"             {comment['snippet']['topLevelComment']['snippet']['textOriginal']}")
        comments_are_shown = True


def update_ideas(topic):
    global popular_videos

    popular_videos = get_popular_videos(api_key, topic)
    if not popular_videos:
        return [], ["Не удалось найти популярные видео по заданной теме."]

    all_titles = [video["title"] for video in popular_videos]
    all_descriptions = [video["description"] for video in popular_videos]
    all_tags = [tag for video in popular_videos for tag in video.get("tags", [])]

    title_word_freq = analyze_text(all_titles)
    description_word_freq = analyze_text(all_descriptions)
    tag_word_freq = analyze_text(all_tags)

    audience_characteristics = analyze_audience_comments(api_key, [video["video_id"] for video in popular_videos])

    # Provide a default empty list if search_related_information returns None
    related_information = search_related_information(api_key, topic) or []

    return generate_video_ideas(topic, popular_videos, audience_characteristics, related_information), []


@app.route('/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    global popular_videos

    if request.method == 'POST':
        topic = request.form['topic']
        video_ideas, error_message = update_ideas(topic)

        return render_template('results.html', video_ideas=video_ideas, popular_videos=popular_videos, error_message=error_message)

    return render_template('index.html')


@app.route('/toggle_comments/<int:selected_video_index>', methods=['POST'])
def toggle_comments(selected_video_index):
    show_comments(selected_video_index)
    return ''


if __name__ == '__main__':
    app.run(debug=True)
