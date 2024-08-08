from flask import Flask, render_template, request, jsonify, session
import os
import openai
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import time
import json
from urllib.parse import urlparse, parse_qs
from googletrans import Translator
from flask_mail import Mail, Message


app = Flask(__name__)
app.secret_key = 'your_secret_key'
CLIENT_SECRET_FILE = 'C:/Users/renub/CODING/BroadRangeAI/Proj_v25/client_secret_144601179279-8cs8egve4cnjpv83gc5omdavi80tbnog.apps.googleusercontent.com.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

openai.api_key = 'sk-proj-uXNgWW9fXybkDpe9ItRYT3BlbkFJNvhn8RoHVzvMJAkcMabW'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'botmyurl@gmail.com'
app.config['MAIL_PASSWORD'] = 'zoki lhrj pncf dnuo'
app.config['MAIL_DEFAULT_SENDER'] = 'botmyurl@gmail.com'

mail = Mail(app)



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

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.netloc == 'www.youtube.com' and parsed_url.path == '/watch':
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v', [None])[0]
        if video_id:
            return video_id
    if parsed_url.netloc == 'youtu.be':
        path_segments = parsed_url.path.split('/')
        if len(path_segments) > 1:
            return path_segments[1]
    return None

def extract_languages_from_error(error_message):
    import re
    language_codes = re.findall(r'\(([^)]+)\)', error_message)
    return language_codes

def get_transcript(video_id, video_title, video_url):
    try:
        transcript_entries = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        transcript_text = ' '.join(entry['text'] for entry in transcript_entries)
        return transcript_text
    except Exception as e:
        error_message = str(e)
        if "Subtitles are disabled" in error_message:
            return {'error': f"Subtitles are disabled for this video: {video_title} ({video_url})"}
        elif "No transcripts were found for any of the requested language codes" in error_message:
            if "(MANUALLY CREATED)" in error_message or "(GENERATED)" in error_message:
                available_languages = extract_languages_from_error(error_message)
                for lang_code in available_languages:
                    try:
                        transcript_entries = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                        transcript_text = ' '.join(entry['text'] for entry in transcript_entries)
                        return transcript_text
                    except:
                        continue
                return {'error': f"Transcript is available in the following languages for video: {video_title} ({video_url})\n"}
            else:
                return {'error': f"Error retrieving transcript for video: {video_title} ({video_url})\n"}
        return {'error': f"Error retrieving transcript for video: {video_title} ({video_url})\n"}

def summarize_text(transcript):
    try:
        if not isinstance(transcript, str):
            transcript = json.dumps(transcript)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Summarize the following video:"},
                {"role": "user", "content": transcript}
            ],
            max_tokens=150,
            temperature=0.5,
            top_p=0.95
        )
        summary = response.choices[0].message['content'].strip()
        return summary
    except Exception as e:
        return f"An error occurred: {e}"



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

@app.route('/preferences', methods=['POST'])
def save_preferences():
    data = request.json
    channels = data.get('channels', [])
    email = session.get('email')
    if email:
        preferences_file = f'preferences_{email}.json'
        with open(preferences_file, 'w') as f:
            json.dump(channels, f)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

@app.route('/process_url', methods=['POST'])
def process_url():
    try:
        urls = request.json['videos']
        summaries = {}        
        for url in urls:
            video_id = extract_video_id(url)
            if video_id:
                video_title = "" 
                transcript = get_transcript(video_id, video_title, url)
                summary = summarize_text(transcript)
                summaries[video_id] = summary
                print(f"\nSummary of {url}:\n {summary}")
        return jsonify({'status': 'success', 'summaries': summaries})
    except Exception as e:
        return jsonify({'status': 'fail', 'error': str(e)})




@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    recipient = data.get('to')
    subject = data.get('subject')
    content = data.get('content')

    try:
        msg = Message(subject, sender='your_email@example.com', recipients=[recipient])
        msg.body = content
        mail.send(msg)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'fail', 'error': str(e)})



@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)