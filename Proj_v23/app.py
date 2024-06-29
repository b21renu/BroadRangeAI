# from flask import Flask, request, render_template, redirect, make_response, flash, jsonify, url_for, session
from flask import Flask, request, render_template, redirect, make_response, flash, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from langdetect import detect
from googletrans import Translator
import fitz 
import openai
import bcrypt
import uuid
from datetime import datetime, timedelta
from python_code import extract_video_id, get_transcript, answer_question_with_transformers, send_email, translate_text, get_function_by_signal, send_signup_email, send_login_email
from jinja2 import Environment, FileSystemLoader


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'

# Configure OpenAI API key
openai.api_key = 'sk-proj-uXNgWW9fXybkDpe9ItRYT3BlbkFJNvhn8RoHVzvMJAkcMabW'

# Initialize Google Translator
translator = Translator()

# Configure Flask-Mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'botmyurl@gmail.com'
app.config['MAIL_PASSWORD'] = 'zoki lhrj pncf dnuo'
app.config['MAIL_DEFAULT_SENDER'] = 'botmyurl@gmail.com'
mail = Mail(app)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)
    session_token = db.Column(db.String(255))
    reset_token = db.Column(db.String(255))
    reset_token_expiration = db.Column(db.DateTime)

# Create database tables within the application context
with app.app_context():
    db.create_all()


# Route for the main page
@app.route('/')
def index():
    """Render the login page."""
    return render_template('login.html')

@app.route('/new', methods=['GET', 'POST'])
def new_page():
    return render_template('youtube.html')


# Helper functions
def validate_password(email, password):
    """Validate user's password."""
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
        return True
    return False


def generate_session_token():
    """Generate a unique session token."""
    return str(uuid.uuid4())

def generate_reset_token():
    """Generate a unique reset token."""
    return str(uuid.uuid4())

def send_reset_email(to_email, reset_token):
    """Send reset password email."""
    msg = Message('Reset Your Password', recipients=[to_email])
    reset_link = url_for('reset_password', token=reset_token, _external=True)
    msg.body = f'Click the link below to reset your password:\n{reset_link}'
    mail.send(msg)

@app.route('/login', methods=['POST'])
def login():
    """Authenticate user and set session token."""
    email = request.form['email']
    password = request.form['password']
    
    if validate_password(email, password):
        session_token = generate_session_token()
        user = User.query.filter_by(email=email).first()
        user.session_token = session_token
        db.session.commit()
        
        # Set session token as a cookie
        response = make_response(redirect('/dashboard'))
        response.set_cookie('session_token', session_token, httponly=True, secure=True)
        return response
    else:
        flash('Invalid email or password', 'error')
        return redirect('/')



@app.route('/dashboard')
def dashboard():
    return render_template('index.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different email.', 'error')
            return redirect('/signup')
        else:
            # Hash the password before storing it
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = User(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect('/')
    return render_template('signup.html')



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password."""
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token and set expiration time
            reset_token = generate_reset_token()
            user.reset_token = reset_token
            user.reset_token_expiration = datetime.now() + timedelta(hours=1)  # Set expiration time (e.g., 1 hour)
            db.session.commit()

            # Send reset password email
            send_reset_email(email, reset_token)
            
            flash('Reset password link has been sent to your email.', 'info')
        else:
            flash('Email not found.', 'error')
        return redirect('/')
    return render_template('forgot_password.html')



@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset."""
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if passwords match
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect('/reset_password/' + token)
        
        # Find the user by the reset token
        user = User.query.filter_by(reset_token=token).first()
        
        if user:
            # Check if the reset token is still valid
            if user.reset_token_expiration >= datetime.now():
                # Update the user's password
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user.password = hashed_password
                # Clear the reset token and its expiration
                user.reset_token = None
                user.reset_token_expiration = None
                db.session.commit()
                
                flash('Password reset successfully. Please log in with your new password.', 'success')
                return redirect('/')
            else:
                flash('Reset token has expired. Please try again.', 'error')
                return redirect('/forgot_password')
        else:
            flash('Invalid or expired reset token.', 'error')
            return redirect('/forgot_password')
    
    return render_template('reset_password.html', token=token)



@app.route('/chatbot')
def chatbot():
    return render_template('page.html')



file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)



# Route to send email
@app.route('/send_email', methods=['POST'])
def send_email_route():
    try:
        subject = "Your Query answered by Multilingual URL ChatBot"
        to_emails = request.form.get('to_emails').split(',')
        extracted_question = request.form.get('question')
        extracted_answer = request.form.get('answer')
        extarcted_url = request.form.get('url')
        extracted_description = request.form.get('description')
        content = render_template(
            'email_template.html',
            url=extarcted_url,
            description=extracted_description,
            question=extracted_question,
            answer=extracted_answer
        )
        print("Content of the email:", content)

        for to_email in to_emails:
            msg = Message(subject, recipients=[to_email])
            msg.html = content
            mail.send(msg)
        return jsonify({'status': 'Email sent successfully!'})
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
    try:
        global transcript  # Use the global variable
        if transcript:
            transcript_with_timestamps2 = [
                f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d} - {entry['text']}"
                for entry in transcript
            ]
            return jsonify({'transcript': transcript_with_timestamps2})
        else:
            return jsonify({'transcript': 'No transcript available'})
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"})


# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        document = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f"An error occurred while extracting text from PDF: {str(e)}")
        return ""


# Function to split text into chunks
def split_text(text, max_tokens):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

# Function to summarize text using OpenAI's GPT-3.5-turbo model with improved parameters
def summarize_large_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following text."},
            {"role": "user", "content": text}
        ],
        max_tokens=150,  # Adjusted for longer summary
        temperature=0.5,  # Lower temperature for more conservative responses
        top_p=0.95  # Higher top_p for more diverse responses
    )
    summary = response.choices[0].message['content'].strip()
    return summary

# Handle file upload
@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist('files[]')
    summaries = []

    for file in uploaded_files:
        try:
            content = extract_text_from_pdf(file)
            detected_language = detect(content)
            if detected_language != 'en':
                translated = translator.translate(content, src=detected_language, dest='en')
                content = translated.text
        except Exception as e:
            return str(e)
        
        summary = summarize_large_text(content)
        summaries.append(summary)

    return jsonify(summaries)
    


def combine_url_and_pdf_content(url_content, pdf_content):
    # You can implement your logic here to combine both contents, such as appending one after the other
    combined_content = url_content + "\n" + pdf_content
    return combined_content

@app.route('/ask_question', methods=['POST'])
def ask_question():
    try:
        question = request.form['question']
        target_language = request.form.get('target_language', 'en')  # Default to English if not provided
        content_type = request.form.get('content_type', 'both')  # Default to using both URL and PDF content
        
        if target_language.lower() == 'other':
            target_language = request.form.get('other_language_textbox', 'en')
        
        # Handle the transcript content
        if content_type == 'url' and not transcript:
            return jsonify({'error': 'No transcript available'})

        if question.lower() == 'transcript':
            transcript_with_timestamps = [
                f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d} - {entry['text']}"
                for entry in transcript
            ]
            return jsonify({'transcript': transcript_with_timestamps})

        if content_type == 'url':
            # Use only URL content
            ai_answer = answer_question_with_transformers(transcript, question, target_language)
            return jsonify({'answer': ai_answer})

        elif content_type == 'pdf':
            if len(request.files.getlist('files[]')) == 0:
                return jsonify({'error': 'No PDF files uploaded'})
            
            pdf_contents = []
            for file in request.files.getlist('files[]'):
                pdf_contents.append(extract_text_from_pdf(file))
            
            combined_pdf_content = "\n".join(pdf_contents)
            ai_answer = answer_question_with_transformers(combined_pdf_content, question, target_language)
            
            return jsonify({'answer': ai_answer})
        
        else:
            # Use both URL and PDF content
            url_content = " ".join([entry['text'] for entry in transcript])
            if 'file' not in request.files:
                return jsonify({'error': 'No PDF file uploaded'})
            pdf_content = extract_text_from_pdf(request.files['file'])
            combined_content = combine_url_and_pdf_content(url_content, pdf_content)
            ai_answer = answer_question_with_transformers(combined_content, question, target_language)
        
        return jsonify({'answer': ai_answer})
    
    except Exception as e:
        return jsonify({'error': f"Error processing question: {str(e)}"})


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
