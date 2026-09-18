import arxiv
import feedparser
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Setup Gemini AI
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_daily_papers():
    arxiv_client = arxiv.Client(page_size=10, delay_seconds=3, num_retries=1)
    
    search = arxiv.Search(
        query="cat:cs.AI",
        max_results=10,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    papers = []
    for result in arxiv_client.results(search):
        papers.append({
            'id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': ', '.join([author.name for author in result.authors]),
            'abstract': result.summary,
            'pdf_url': result.pdf_url,
            'date': result.published.strftime("%Y-%m-%d")
        })
    return papers

def fetch_ai_news():
    feed = feedparser.parse('https://news.google.com/rss/search?q=Artificial+Intelligence&hl=en-US&gl=US&ceid=US:en')
    news = []
    for entry in feed.entries[:15]:
        news.append({
            'title': entry.title,
            'link': entry.link,
            'date': entry.published
        })
    return news

def analyze_paper_with_ai(abstract):
    prompt = f"""
    You are an AI expert. Analyze this research paper abstract:
    {abstract}
    
    1. Give a relevance score (0-100%) on how much this relates specifically to AI, Machine Learning, and Python.
    2. Write a Simple Summary (understandable by a beginner).
    3. Write a Detailed Explanation (for a developer/researcher).
    
    Format your response EXACTLY like this:
    Relevance Score: [Score]%
    Simple Summary: [Your simple summary]
    Detailed Explanation: [Your detailed explanation]
    """
    
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
    )
    return response.text

def chat_about_paper(abstract, user_question):
    prompt = f"""
    Context: Research Paper Abstract: {abstract}
    User Question: {user_question}
    Answer the question based ONLY on the context of this research paper. Keep it simple and helpful.
    """
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
    )
    return response.text