import googleapiclient.discovery
import googleapiclient.errors


# Функция для получения списка популярных видео по заданной теме
def get_popular_videos(api_key, topic):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    try:
        request = youtube.search().list(
            part="snippet",
            q=topic,
            type="video",
            order="viewCount",
            maxResults=10
        )
        response = request.execute()

        popular_videos = []
        for item in response["items"]:
            video_data = {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "tags": item["snippet"].get("tags", [])
            }
            popular_videos.append(video_data)

        return popular_videos

    except googleapiclient.errors.HttpError as e:
        print("An error occurred:", e)
        return None


# Функция для получения комментариев к видео
def get_video_comments(api_key, video_id):
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
            comment = {
                "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                "likeCount": item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
            }
            comments.append(comment)

        # Сортируем комментарии по количеству лайков в убывающем порядке
        comments.sort(key=lambda x: x["likeCount"], reverse=True)

        # Возвращаем только топ 10 комментариев
        top_10_comments = [comment["text"] for comment in comments[:10]]
        return top_10_comments

    except googleapiclient.errors.HttpError as e:
        print("An error occurred:", e)
        return None

