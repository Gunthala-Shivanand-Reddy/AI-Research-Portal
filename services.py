import arxiv
import feedparser
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Safe getter for Gemini Client so the server doesn't crash on startup!
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY. Check Render Dashboard!")
    return genai.Client(api_key=api_key)

def fetch_daily_papers():
    arxiv_client = arxiv.Client(page_size=10, delay_seconds=3, num_retries=1)
    
    search = arxiv.Search(
        query='all:"generative ai" OR all:"natural language processing" OR all:"LLM" OR all:"NLP"', 
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
    # Updated URL to specifically search for Generative AI and NLP news
    url = 'https://news.google.com/rss/search?q=%22Generative+AI%22+OR+%22Natural+Language+Processing%22+OR+LLM&hl=en-US&gl=US&ceid=US:en'
    feed = feedparser.parse(url)
    news = []
    for entry in feed.entries[:15]:
        news.append({
            'title': entry.title,
            'link': entry.link,
            'date': entry.published
        })
    return news

def analyze_paper_with_ai(abstract):
    client = get_gemini_client()
    prompt = f"""
    You are an AI expert. Analyze this research paper abstract:
    {abstract}
    
    1. Give a relevance score (0-100%) on how much this relates specifically to Generative AI, Large Language Models, and NLP.
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
    client = get_gemini_client()
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

def fetch_paper_by_id(paper_id):
    import arxiv
    search = arxiv.Search(id_list=[paper_id])
    try:
        # Get just this specific paper
        result = next(arxiv.Client().results(search))
        return {
            'id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': ', '.join([author.name for author in result.authors]),
            'date': result.published.strftime("%Y-%m-%d"),
            'abstract': result.summary,
            'pdf_url': result.pdf_url
        }
    except Exception:
        return None