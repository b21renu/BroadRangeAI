from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse, parse_qs
from python_code import extract_video_id, get_transcript, answer_question_with_transformers, send_email, translate_text
from python_code import get_function_by_signal, send_signup_email, send_login_email
#from flask import redirect, url_for

app = Flask(__name__)
transcript = []

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        to_email = request.form['email']
        signal = 'login'  # Set the signal for index
        email_function = get_function_by_signal(signal)

        if email_function:
            email_function(to_email)
            return render_template('index.html')
        else:
            return render_template('error.html', message='Invalid signal')
    else:
        return render_template('index.html')
    
@app.route('/signup', methods=['GET','POST'])
def signup_user():
    if request.method == 'POST':
        to_email = request.form['email']
        signal = 'signup'  # Set the signal for signup
        email_function = get_function_by_signal(signal)

        if email_function:
            email_function(to_email)
            return render_template('signup-user.html')
        else:
            return render_template('error.html', message='Invalid signal')
    else:
        return render_template('signup-user.html')
    
@app.route('/send', methods=['POST'])
def send_email():
    if request.method == 'POST':
        to_email = request.form['email']
        signal = request.form['signal']
        email_function = get_function_by_signal(signal)

        if email_function:
            email_function(to_email)
            return render_template('page.html')
        else:
            return render_template('error.html', message='Invalid signal')

@app.route('/send_email', methods=['POST'])
def send_email_route():
    try:
        to_email = request.form['to_email']
        subject = request.form['subject']
        content = request.form['content']
        signal = 'email'
        email_function = get_function_by_signal(signal)
        
        if email_function:
            email_function(to_email, subject, content)
            return jsonify({'status': 'Email sent successfully!'})
        else:
            return jsonify({'error': 'Invalid signal'})
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"})

@app.route('/process_url', methods=['POST'])
def process_url():
    try:
        global transcript  # Use the global variable
        youtube_url = request.form['youtube_url']
        video_id = extract_video_id(youtube_url)
        transcript = get_transcript(video_id)
        return jsonify(transcript)
    except Exception as e:
        return jsonify({'error': f"An error occurred: {e}"})

@app.route('/transcript_print', methods=['POST'])
def transcript_print():
    # try:
        if transcript:
            transcript_with_timestamps2 = [
                f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d} - {entry['text']}"
                for entry in transcript
            ]
            return jsonify({'transcript': transcript_with_timestamps2})
        else:
            return jsonify({'transcript': 'No transcript available'})
    # except Exception as e:
        # error_message = str(e)
        # if "video language" in error_message.lower():
        #     return jsonify({'error': 'Video language is different'})
        # else:
        #     return jsonify({'error': 'An error occurred during processing'})


@app.route('/ask_question', methods=['POST'])
def ask_question():
    try:
        question = request.form['question']
        target_language = request.form.get('target_language', 'en')  # Default to English if not provided

        if target_language.lower() == 'other':
            target_language = request.form.get('other_language_textbox', 'en')
            
        if not transcript:
            return jsonify({'error': 'No transcript available'})

        if question.lower() == 'transcript':
            transcript_with_timestamps = [
                f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d} - {entry['text']}"
                for entry in transcript
            ]
            return jsonify({'transcript': transcript_with_timestamps})
        
        ai_answer = answer_question_with_transformers(transcript, question, target_language)
        return jsonify({'answer': ai_answer})
    except Exception as e:
        return jsonify({'error': f"Error processing question: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)