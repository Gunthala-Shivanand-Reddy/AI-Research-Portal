from flask import Flask, render_template, request, jsonify
import services

app = Flask(__name__)

# ===== SECURITY SETTINGS =====
# Prevent clickjacking (stops hackers from embedding your site inside theirs)
# Prevent XSS attacks (stops hackers from injecting scripts)
# Hide that you are using Flask (hackers target known frameworks)
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Remove the "Server: Flask" header so hackers can't identify your tech
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ===== RATE LIMITING (Prevents spam/attacks) =====
from functools import wraps
import time

request_log = {}

def rate_limit(max_requests=30, window=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            # Clean old entries
            request_log[ip] = [t for t in request_log.get(ip, []) if now - t < window]
            if len(request_log[ip]) >= max_requests:
                return "Too many requests. Please wait a minute.", 429
            request_log[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ===== ROUTES (Read-Only, no edit/delete/upload allowed) =====
papers_db = {}

@app.route('/')
@rate_limit()
def dashboard():
    raw_papers = services.fetch_daily_papers()
    for p in raw_papers:
        papers_db[p['id']] = p
    return render_template('index.html', papers=raw_papers)

@app.route('/news')
@rate_limit()
def news():
    ai_news = services.fetch_ai_news()
    return render_template('news.html', news=ai_news)

@app.route('/paper/<paper_id>')
@rate_limit()
def view_paper(paper_id):
    paper = papers_db.get(paper_id)
    if not paper:
        return "Paper not found", 404
    explanation = services.analyze_paper_with_ai(paper['abstract'])
    return render_template('paper.html', paper=paper, explanation=explanation)

@app.route('/chat', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def chat():
    data = request.json
    if not data or not data.get('paper_id') or not data.get('question'):
        return jsonify({"answer": "Invalid request."}), 400
    
    paper_id = data.get('paper_id')
    question = data.get('question')
    
    # Limit question length to prevent abuse
    if len(question) > 500:
        return jsonify({"answer": "Question too long. Keep it under 500 characters."}), 400
    
    paper = papers_db.get(paper_id)
    if not paper:
        return jsonify({"answer": "Paper not found."}), 404
    
    answer = services.chat_about_paper(paper['abstract'], question)
    return jsonify({"answer": answer})

# Block all other routes (no one can access hidden files or admin pages)
@app.errorhandler(404)
def not_found(e):
    return "Page not found.", 404

@app.errorhandler(405)
def method_not_allowed(e):
    return "Method not allowed.", 405

if __name__ == '__main__':
    app.run(debug=False, port=5000)