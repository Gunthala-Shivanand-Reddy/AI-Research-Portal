from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import services
import os

app = Flask(__name__)
# Security key for the browser session
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-123")
# The password to enter the site (Defaults to '12345' if you don't set it in Render)
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "12345")

# ===== LOGIN SYSTEM =====
@app.before_request
def require_login():
    # Allow access to the login page and CSS styling without a password
    if request.endpoint in ['login', 'static']:
        return
    # If they are not logged in, force them back to the login page
    if not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Check if the password they typed matches your secret password
        if request.form.get('password') == SITE_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "Incorrect Access Code"
    return render_template('login.html', error=error)

# ===== SECURITY HEADERS =====
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ===== ROUTES =====
papers_db = {}

@app.route('/')
def dashboard():
    raw_papers = services.fetch_daily_papers()
    for p in raw_papers:
        papers_db[p['id']] = p
    return render_template('index.html', papers=raw_papers)

@app.route('/news')
def news():
    ai_news = services.fetch_ai_news()
    return render_template('news.html', news=ai_news)

@app.route('/paper/<paper_id>')
def view_paper(paper_id):
    paper = papers_db.get(paper_id)
    if not paper:
        return "Paper not found", 404
    explanation = services.analyze_paper_with_ai(paper['abstract'])
    return render_template('paper.html', paper=paper, explanation=explanation)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    paper_id = data.get('paper_id')
    question = data.get('question')
    
    paper = papers_db.get(paper_id)
    answer = services.chat_about_paper(paper['abstract'], question)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=False, port=5000)