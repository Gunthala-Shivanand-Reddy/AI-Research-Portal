from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import timedelta
import services
import database
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-123")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=10)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ===== LOGIN GUARD =====
@app.before_request
def require_login():
    session.permanent = True
    allowed = ['login', 'signup', 'auth_callback', 'verify_token',
               'forgot_password', 'reset_password', 'update_password', 'static']
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

# ===== AUTH ROUTES =====

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            database.create_user(name, email, password)
            return render_template('check_email.html', email=email)
        except Exception as e:
            error = f"Error creating account: {str(e)}"
    return render_template('signup.html', error=error)

@app.route('/auth/callback')
def auth_callback():
    return render_template('auth_callback.html')

@app.route('/auth/verify-token', methods=['POST'])
def verify_token():
    data = request.json
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    try:
        db = database.get_db()
        result = db.auth.set_session(access_token, refresh_token)
        if result.user:
            session['logged_in'] = True
            session['user_email'] = result.user.email
            session['user_name'] = result.user.user_metadata.get('name', 'Researcher')
            return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False})

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = database.login_user(email, password)
            session['logged_in'] = True
            session['user_email'] = user.email
            session['user_name'] = user.user_metadata.get('name', 'Researcher')
            return redirect(url_for('dashboard'))
        except Exception as e:
            error_msg = str(e)
            if "Email not confirmed" in error_msg:
                error = "Please verify your email first. Check your inbox for the verification link!"
            elif "Invalid login credentials" in error_msg:
                error = "Incorrect email or password."
            else:
                error = f"Login error: {error_msg}"
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
        try:
            database.send_password_reset(email)
            success = "Password reset link sent! Check your email inbox."
        except Exception as e:
            error = f"Error: {str(e)}"
    return render_template('forgot_password.html', error=error, success=success)

@app.route('/reset-password')
def reset_password():
    return render_template('reset_password.html')

@app.route('/auth/update-password', methods=['POST'])
def update_password():
    data = request.json
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    new_password = data.get('password')
    try:
        db = database.get_db()
        db.auth.set_session(access_token, refresh_token)
        db.auth.update_user({"password": new_password})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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