# from flask import Flask, render_template, request, jsonify, session
# import os
# import openai
# import pickle
# from datetime import datetime, timedelta
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from google.auth.transport.requests import Request
# from googleapiclient.errors import HttpError
# import time
# import json
# from urllib.parse import urlparse, parse_qs
# from youtube_transcript_api import YouTubeTranscriptApi
# from googletrans import Translator
# # from python_code import extract_video_id, get_transcript

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'
# CLIENT_SECRET_FILE = '/Users/muralidharbojja/Downloads/Proj_v25/client_secret_144601179279-8cs8egve4cnjpv83gc5omdavi80tbnog.apps.googleusercontent.com.json'
# SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# # Configure OpenAI API key
# openai.api_key = 'sk-proj-uXNgWW9fXybkDpe9ItRYT3BlbkFJNvhn8RoHVzvMJAkcMabW'

# def get_authenticated_service():
#     email = session.get('email')
#     if not email:
#         return None

#     credentials = None
#     token_file = f'token_{email}.pickle'

#     if os.path.exists(token_file):
#         with open(token_file, 'rb') as token:
#             credentials = pickle.load(token)

#     if not credentials or not credentials.valid:
#         if credentials and credentials.expired and credentials.refresh_token:
#             credentials.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
#             credentials = flow.run_local_server(port=8080)
#             with open(token_file, 'wb') as token:
#                 pickle.dump(credentials, token)

#     return build('youtube', 'v3', credentials=credentials)

# def list_subscriptions(youtube):
#     subscriptions = []
#     request = youtube.subscriptions().list(
#         part='snippet,contentDetails',
#         mine=True,
#         maxResults=50
#     )

#     while request:
#         try:
#             response = request.execute()
#         except HttpError as e:
#             if e.resp.status == 403:
#                 time.sleep(3600)
#                 continue
#             else:
#                 return []

#         for subscription in response['items']:
#             snippet = subscription['snippet']
#             channel_id = snippet['resourceId']['channelId']
#             channel_title = snippet['title']
#             subscriptions.append({'channel_id': channel_id, 'channel_title': channel_title})

#         request = youtube.subscriptions().list_next(request, response)
    
#     return subscriptions

# def get_videos_from_channel_today(youtube, channel_id):
#     today = datetime.utcnow().date()
#     today_start = datetime(today.year, today.month, today.day)
#     today_end = today_start + timedelta(days=1)

#     request = youtube.search().list(
#         part='snippet',
#         channelId=channel_id,
#         publishedAfter=today_start.isoformat("T") + "Z",
#         publishedBefore=today_end.isoformat("T") + "Z",
#         maxResults=50
#     )

#     try:
#         response = request.execute()
#     except HttpError as e:
#         if e.resp.status == 403:
#             return []
#         else:
#             return []

#     videos = []
#     for item in response.get('items', []):
#         if item['id']['kind'] == 'youtube#video':
#             video_id = item['id']['videoId']
#             video_title = item['snippet']['title']
#             published_at = item['snippet']['publishedAt']
#             videos.append({'video_id': video_id, 'video_title': video_title, 'published_at': published_at})
    
#     videos.sort(key=lambda x: x['published_at'], reverse=True)
#     return videos

# def extract_video_id(url):
#     parsed_url = urlparse(url)

#     if parsed_url.netloc == 'www.youtube.com' and parsed_url.path == '/watch':
#         query_params = parse_qs(parsed_url.query)
#         video_id = query_params.get('v', [None])[0]
#         if video_id:
#             return video_id

#     if parsed_url.netloc == 'youtu.be':
#         path_segments = parsed_url.path.split('/')
#         if len(path_segments) > 1:
#             return path_segments[1]

#     return None

# def get_transcript(video_id):
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(video_id)
#         return transcript
#     except KeyError as ke:
#         print(f"KeyError in transcript: {ke}")
#         return []
#     except Exception as e:
#         print(f"Error retrieving transcript: {e}")
#         return []

# @app.route('/')
# def index():
#     return render_template('youtube.html')

# # @app.route('/new_page')
# # def new_page():
# #     return render_template('youtube.html')

# @app.route('/email', methods=['POST'])
# def email():
#     data = request.json
#     email = data.get('email')
#     session['email'] = email
#     youtube = get_authenticated_service()
#     if youtube:
#         return jsonify({'status': 'success'})
#     else:
#         return jsonify({'status': 'fail'})

# @app.route('/subscriptions', methods=['GET'])
# def subscriptions():
#     youtube = get_authenticated_service()
#     if not youtube:
#         return jsonify({'status': 'fail', 'subscriptions': []})

#     subscriptions = list_subscriptions(youtube)
#     return jsonify({'status': 'success', 'subscriptions': subscriptions})

# @app.route('/channel/<channel_id>', methods=['GET'])
# def channel_videos(channel_id):
#     youtube = get_authenticated_service()
#     if not youtube:
#         return jsonify({'status': 'fail', 'videos': []})

#     videos = get_videos_from_channel_today(youtube, channel_id)
#     return jsonify({'status': 'success', 'videos': videos})

# @app.route('/preferences', methods=['POST'])
# def save_preferences():
#     data = request.json
#     channels = data.get('channels', [])
#     email = session.get('email')
#     if email:
#         preferences_file = f'preferences_{email}.json'
#         with open(preferences_file, 'w') as f:
#             json.dump(channels, f)
#         return jsonify({'status': 'success'})
#     return jsonify({'status': 'fail'})

# @app.route('/process_url', methods=['POST'])
# def process_url():
#     try:
#         urls = request.json['videos']
#         transcripts = {}
#         for url in urls:
#             video_id = extract_video_id(url)
#             if video_id:
#                 transcript = get_transcript(video_id)
#                 transcripts[video_id] = transcript
#         return jsonify({'status': 'success', 'transcripts': transcripts})
#     except Exception as e:
#         return jsonify({'status': 'fail', 'error': str(e)})

# # @app.route('/summarize_videos', methods=['POST'])
# # def summarize_videos():
# #     try:
# #         transcripts = request.json['transcripts']
# #         summaries = {}
# #         for video_id, transcript in transcripts.items():
# #             if transcript:
# #                 transcript_text = ' '.join(entry['text'] for entry in transcript)
# #                 response = openai.Completion.create(
# #                     engine="davinci",
# #                     prompt=transcript_text,
# #                     max_tokens=150,
# #                     temperature=0.3,
# #                     top_p=1.0,
# #                     frequency_penalty=0.0,
# #                     presence_penalty=0.0,
# #                     stop=["\n"]
# #                 )
# #                 summary = response['choices'][0]['text'].strip()
# #                 summaries[video_id] = summary
# #         return jsonify({'status': 'success', 'summaries': summaries})
# #     except Exception as e:
# #         return jsonify({'status': 'fail', 'error': str(e)})


# @app.route('/summarize_videos', methods=['POST'])
# def summarize_videos():
#     try:
#         global transcript  # Use the global variable
#         if transcript:
#             transcript_with_timestamps2 = [
#                 f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d} - {entry['text']}"
#                 for entry in transcript
#             ]
#             return jsonify({'transcript': transcript_with_timestamps2})
#         else:
#             return jsonify({'transcript': 'No transcript available'})
#     except Exception as e:
#         return jsonify({'error': f"An error occurred: {str(e)}"})

#     # try:
#     #     transcripts = request.json['transcripts']
#     #     summaries = {}
        
#     #     translator = Translator()

#     #     for video_id, transcript in transcripts.items():
#     #         if transcript:
#     #             transcript_text = ' '.join(entry['text'] for entry in transcript)
                
#     #             # Translate transcript to English
#     #             translated_text = translator.translate(transcript_text, src='auto', dest='en').text
                
#     #             # Summarize translated text using OpenAI's GPT-3
#     #             response = openai.Completion.create(
#     #                 engine="davinci",
#     #                 prompt=translated_text,
#     #                 max_tokens=150,
#     #                 temperature=0.3,
#     #                 top_p=1.0,
#     #                 frequency_penalty=0.0,
#     #                 presence_penalty=0.0,
#     #                 stop=["\n"]
#     #             )
                
#     #             summary = response['choices'][0]['text'].strip()
#     #             summaries[video_id] = summary
        
#     #     return jsonify({'status': 'success', 'summaries': summaries})
    
#     # except Exception as e:
#     #     return jsonify({'status': 'fail', 'error': str(e)})


# @app.route('/favicon.ico')
# def favicon():
#     return '', 204

# if __name__ == '__main__':
#     app.run(debug=True)






# LATEST CODE

# from flask import Flask, render_template, request, jsonify, session
# import os
# import openai
# import pickle
# from datetime import datetime, timedelta
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from google.auth.transport.requests import Request
# from googleapiclient.errors import HttpError
# from youtube_transcript_api import YouTubeTranscriptApi
# import time
# import json
# from urllib.parse import urlparse, parse_qs
# from googletrans import Translator

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'
# CLIENT_SECRET_FILE = '/path/to/your/client_secret.json'
# SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# # Configure OpenAI API key
# openai.api_key = 'your_openai_api_key'

# def get_authenticated_service():
#     email = session.get('email')
#     if not email:
#         return None

#     credentials = None
#     token_file = f'token_{email}.pickle'

#     if os.path.exists(token_file):
#         with open(token_file, 'rb') as token:
#             credentials = pickle.load(token)

#     if not credentials or not credentials.valid:
#         if credentials and credentials.expired and credentials.refresh_token:
#             credentials.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
#             credentials = flow.run_local_server(port=8080)
#             with open(token_file, 'wb') as token:
#                 pickle.dump(credentials, token)

#     return build('youtube', 'v3', credentials=credentials)

# def list_subscriptions(youtube):
#     subscriptions = []
#     request = youtube.subscriptions().list(
#         part='snippet,contentDetails',
#         mine=True,
#         maxResults=50
#     )

#     while request:
#         try:
#             response = request.execute()
#         except HttpError as e:
#             if e.resp.status == 403:
#                 time.sleep(3600)
#                 continue
#             else:
#                 return []

#         for subscription in response['items']:
#             snippet = subscription['snippet']
#             channel_id = snippet['resourceId']['channelId']
#             channel_title = snippet['title']
#             subscriptions.append({'channel_id': channel_id, 'channel_title': channel_title})

#         request = youtube.subscriptions().list_next(request, response)
    
#     return subscriptions

# def get_videos_from_channel_today(youtube, channel_id):
#     today = datetime.utcnow().date()
#     today_start = datetime(today.year, today.month, today.day)
#     today_end = today_start + timedelta(days=1)

#     request = youtube.search().list(
#         part='snippet',
#         channelId=channel_id,
#         publishedAfter=today_start.isoformat("T") + "Z",
#         publishedBefore=today_end.isoformat("T") + "Z",
#         maxResults=50
#     )

#     try:
#         response = request.execute()
#     except HttpError as e:
#         if e.resp.status == 403:
#             return []
#         else:
#             return []

#     videos = []
#     for item in response.get('items', []):
#         if item['id']['kind'] == 'youtube#video':
#             video_id = item['id']['videoId']
#             video_title = item['snippet']['title']
#             published_at = item['snippet']['publishedAt']
#             videos.append({'video_id': video_id, 'video_title': video_title, 'published_at': published_at})
    
#     videos.sort(key=lambda x: x['published_at'], reverse=True)
#     return videos

# def extract_video_id(url):
#     parsed_url = urlparse(url)

#     if parsed_url.netloc == 'www.youtube.com' and parsed_url.path == '/watch':
#         query_params = parse_qs(parsed_url.query)
#         video_id = query_params.get('v', [None])[0]
#         if video_id:
#             return video_id

#     if parsed_url.netloc == 'youtu.be':
#         path_segments = parsed_url.path.split('/')
#         if len(path_segments) > 1:
#             return path_segments[1]

#     return None

# def get_transcript(video_id):
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(video_id)
#         return transcript
#     except Exception as e:
#         print(f"Error retrieving transcript: {e}")
#         return []

# @app.route('/')
# def index():
#     return render_template('youtube.html')

# @app.route('/email', methods=['POST'])
# def email():
#     data = request.json
#     email = data.get('email')
#     session['email'] = email
#     youtube = get_authenticated_service()
#     if youtube:
#         return jsonify({'status': 'success'})
#     else:
#         return jsonify({'status': 'fail'})

# @app.route('/subscriptions', methods=['GET'])
# def subscriptions():
#     youtube = get_authenticated_service()
#     if not youtube:
#         return jsonify({'status': 'fail', 'subscriptions': []})

#     subscriptions = list_subscriptions(youtube)
#     return jsonify({'status': 'success', 'subscriptions': subscriptions})

# @app.route('/channel/<channel_id>', methods=['GET'])
# def channel_videos(channel_id):
#     youtube = get_authenticated_service()
#     if not youtube:
#         return jsonify({'status': 'fail', 'videos': []})

#     videos = get_videos_from_channel_today(youtube, channel_id)
#     return jsonify({'status': 'success', 'videos': videos})

# @app.route('/preferences', methods=['POST'])
# def save_preferences():
#     data = request.json
#     channels = data.get('channels', [])
#     email = session.get('email')
#     if email:
#         preferences_file = f'preferences_{email}.json'
#         with open(preferences_file, 'w') as f:
#             json.dump(channels, f)
#         return jsonify({'status': 'success'})
#     return jsonify({'status': 'fail'})

# @app.route('/process_url', methods=['POST'])
# def process_url():
#     try:
#         urls = request.json['videos']
#         transcripts = {}
#         for url in urls:
#             video_id = extract_video_id(url)
#             if video_id:
#                 transcript = get_transcript(video_id)
#                 transcripts[video_id] = transcript
#         return jsonify({'status': 'success', 'transcripts': transcripts})
#     except Exception as e:
#         return jsonify({'status': 'fail', 'error': str(e)})

# @app.route('/summarize_videos', methods=['POST'])
# def summarize_videos():
#     try:
#         transcripts = request.json['transcripts']
#         summaries = {}
        
#         translator = Translator()

#         for video_id, transcript in transcripts.items():
#             if transcript:
#                 transcript_text = ' '.join(entry['text'] for entry in transcript)
                
#                 # Translate transcript to English
#                 translated_text = translator.translate(transcript_text, src='auto', dest='en').text
                
#                 # Summarize translated text using OpenAI's GPT-3
#                 response = openai.Completion.create(
#                     engine="davinci",
#                     prompt=translated_text,
#                     max_tokens=150,
#                     temperature=0.3,
#                     top_p=1.0,
#                     frequency_penalty=0.0,
#                     presence_penalty=0.0,
#                     stop=["\n"]
#                 )
                
#                 summary = response['choices'][0]['text'].strip()
#                 summaries[video_id] = summary
        
#         return jsonify({'status': 'success', 'summaries': summaries})
    
#     except Exception as e:
#         return jsonify({'status': 'fail', 'error': str(e)})

# @app.route('/favicon.ico')
# def favicon():
#     return '', 204

# if __name__ == '__main__':
#     app.run(debug=True)
