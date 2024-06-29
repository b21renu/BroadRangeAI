from flask import Flask, render_template, request, jsonify, session
import os
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CLIENT_SECRET_FILE = 'C:/Users/renub/CODING/BroadRangeAI/Proj_v23/client_secret_144601179279-8cs8egve4cnjpv83gc5omdavi80tbnog.apps.googleusercontent.com.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']


@app.route('/new_page')
def new_page():
    return render_template('youtube.html')


def get_authenticated_service():
    email = session.get('email')
    if not email:
        return None

    credentials = None
    token_file = f'token_{email}.pickle'

    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            credentials = flow.run_local_server(port=8080)
            with open(token_file, 'wb') as token:
                pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def list_subscriptions(youtube):
    subscriptions = []
    request = youtube.subscriptions().list(
        part='snippet,contentDetails',
        mine=True,
        maxResults=50
    )

    while request:
        try:
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 403:
                time.sleep(3600)
                continue
            else:
                return []

        for subscription in response['items']:
            snippet = subscription['snippet']
            channel_id = snippet['resourceId']['channelId']
            channel_title = snippet['title']
            subscriptions.append({'channel_id': channel_id, 'channel_title': channel_title})

        request = youtube.subscriptions().list_next(request, response)
    
    return subscriptions

def get_videos_from_channel_today(youtube, channel_id):
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)

    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        publishedAfter=today_start.isoformat("T") + "Z",
        publishedBefore=today_end.isoformat("T") + "Z",
        maxResults=50
    )

    try:
        response = request.execute()
    except HttpError as e:
        if e.resp.status == 403:
            return []
        else:
            return []

    videos = []
    for item in response.get('items', []):
        if item['id']['kind'] == 'youtube#video':
            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']
            videos.append({'video_id': video_id, 'video_title': video_title, 'published_at': published_at})
    
    videos.sort(key=lambda x: x['published_at'], reverse=True)
    return videos

@app.route('/')
def index():
    return render_template('youtube.html')

@app.route('/email', methods=['POST'])
def email():
    data = request.json
    email = data.get('email')
    session['email'] = email
    youtube = get_authenticated_service()
    if youtube:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'fail'})

@app.route('/subscriptions', methods=['GET'])
def subscriptions():
    youtube = get_authenticated_service()
    if not youtube:
        return jsonify({'status': 'fail', 'subscriptions': []})

    subscriptions = list_subscriptions(youtube)
    return jsonify({'status': 'success', 'subscriptions': subscriptions})

@app.route('/channel/<channel_id>', methods=['GET'])
def channel_videos(channel_id):
    youtube = get_authenticated_service()
    if not youtube:
        return jsonify({'status': 'fail', 'videos': []})

    videos = get_videos_from_channel_today(youtube, channel_id)
    return jsonify({'status': 'success', 'videos': videos})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)