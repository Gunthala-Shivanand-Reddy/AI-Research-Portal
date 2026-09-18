from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import timedelta
import services
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-123")
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "12345")

# Make the VIP login stamp last for 30 days so you don't get logged out randomly!
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# ===== LOGIN SYSTEM =====
@app.before_request
def require_login():
    session.permanent = True # Apply the 30-day rule
    if request.endpoint in ['login', 'static']:
        return
    if not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
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

@app.route('/paper/<path:paper_id>')
def view_paper(paper_id):
    # Try to find it in memory first
    paper = papers_db.get(paper_id)
    
    # If the server forgot it, fetch it directly!
    if not paper:
        paper = services.fetch_paper_by_id(paper_id)
        if not paper:
            return "Paper not found", 404
        papers_db[paper_id] = paper # Save it back to memory
        
    try:
        explanation = services.analyze_paper_with_ai(paper['abstract'])
    except Exception as e:
        explanation = "AI Error: Gemini is busy or taking too long. Please refresh the page."
        
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
        answer = "Sorry, the AI is currently too busy to answer. Please try again."
        
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=False, port=5000)