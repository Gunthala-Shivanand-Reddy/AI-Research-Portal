from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import timedelta
import services
import database
import email_utils
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-123")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=10)

# ===== LOGIN GUARD =====
@app.before_request
def require_login():
    session.permanent = True
    allowed = ['login', 'signup', 'verify_otp', 'forgot_password', 'reset_password', 'static']
    if request.endpoint in allowed:
        return
    if not session.get('logged_in'):
        return redirect(url_for('login'))

# ===== SECURITY HEADERS =====
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ===== AUTH ROUTES =====

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        existing = database.get_user_by_email(email)
        if existing:
            error = "An account with this email already exists."
        else:
            try:
                user, otp = database.create_user(name, email, password)
                email_utils.send_otp_email(email, otp, purpose="verification")
                session['pending_email'] = email
                return redirect(url_for('verify_otp'))
            except Exception as e:
                error = f"Error creating account: {str(e)}"

    return render_template('signup.html', error=error)

@app.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    error = None
    email = session.get('pending_email')
    if not email:
        return redirect(url_for('login'))

    if request.method == 'POST':
        otp = request.form.get('otp')
        if database.verify_user_otp(email, otp):
            session.pop('pending_email', None)
            session['logged_in'] = True
            session['user_email'] = email
            return redirect(url_for('dashboard'))
        else:
            error = "Incorrect OTP. Please try again."

    return render_template('verify_otp.html', email=email, error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = database.get_user_by_email(email)

        if not user:
            error = "No account found with this email."
        elif not user['is_verified']:
            otp = email_utils.generate_otp()
            database.update_user_otp(email, otp)
            email_utils.send_otp_email(email, otp)
            session['pending_email'] = email
            return redirect(url_for('verify_otp'))
        elif not database.check_password(user, password):
            error = "Incorrect password."
        else:
            session['logged_in'] = True
            session['user_email'] = email
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form.get('email')
        user = database.get_user_by_email(email)
        if not user:
            error = "No account found with this email."
        else:
            otp = email_utils.generate_otp()
            database.update_user_otp(email, otp)
            email_utils.send_otp_email(email, otp, purpose="reset")
            session['reset_email'] = email
            return redirect(url_for('reset_password'))

    return render_template('forgot_password.html', error=error, success=success)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    error = None
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        otp = request.form.get('otp')
        new_password = request.form.get('password')
        if database.verify_user_otp(email, otp):
            database.update_user_password(email, new_password)
            session.pop('reset_email', None)
            return redirect(url_for('login'))
        else:
            error = "Incorrect OTP. Please try again."

    return render_template('reset_password.html', error=error)

# ===== MAIN ROUTES =====
papers_db = {}

@app.route('/')
def dashboard():
    raw_papers = services.fetch_daily_papers()
    for p in raw_papers:
        papers_db[p['id']] = p
    user_name = session.get('user_name', 'Researcher')
    return render_template('index.html', papers=raw_papers, user_name=user_name)

@app.route('/news')
def news():
    ai_news = services.fetch_ai_news()
    return render_template('news.html', news=ai_news)

@app.route('/paper/<path:paper_id>')
def view_paper(paper_id):
    paper = papers_db.get(paper_id)
    if not paper:
        paper = services.fetch_paper_by_id(paper_id)
        if not paper:
            return "Paper not found", 404
        papers_db[paper_id] = paper

    try:
        explanation = services.analyze_paper_with_ai(paper['abstract'])
    except Exception:
        explanation = "AI is currently busy. Please refresh the page to try again."

    return render_template('paper.html', paper=paper, explanation=explanation)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    paper_id = data.get('paper_id')
    question = data.get('question')
    paper = papers_db.get(paper_id)
    if not paper:
        paper = services.fetch_paper_by_id(paper_id)
    try:
        answer = services.chat_about_paper(paper['abstract'], question)
    except Exception:
        answer = "The AI is currently busy. Please try again in a moment."
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=False, port=5000)