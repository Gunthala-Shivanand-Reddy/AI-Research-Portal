import arxiv
import feedparser
import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Safe getter for Gemini client to prevent startup crashes if key is missing
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables!")
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
    feed_url = 'https://hnrss.org/newest?q=AI+OR+Machine+Learning+OR+LLM'
    feed = feedparser.parse(feed_url)
    
    news = []
    for entry in feed.entries[:10]:
        news.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.get('published', 'Recently'),
            'summary': entry.get('summary', 'No summary available.')
        })
    return news

def fetch_paper_by_id(paper_id):
    arxiv_client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    
    try:
        result = next(arxiv_client.results(search))
        return {
            'id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': ', '.join([author.name for author in result.authors]),
            'abstract': result.summary,
            'pdf_url': result.pdf_url,
            'date': result.published.strftime("%Y-%m-%d")
        }
    except StopIteration:
        return None

def analyze_paper_with_ai(abstract):
    client = get_gemini_client()
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    last_error = ""
    
    for model in models_to_try:
        for attempt in range(2): 
            try:
                prompt = f"Explain this AI research paper abstract in simple terms for a beginner:\n\n{abstract}"
                response = client.models.generate_content(model=model, contents=prompt)
                return response.text
            except Exception as e:
                last_error = str(e)
                if "503" in last_error or "429" in last_error:
                    time.sleep(2)
                    continue
                else:
                    break # Hard error, move to next model
                    
    # THIS WILL NOW SHOW US THE EXACT GOOGLE ERROR
    raise Exception(f"REAL ERROR: {last_error}")

def chat_about_paper(abstract, question):
    client = get_gemini_client()
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    last_error = ""
    
    for model in models_to_try:
        for attempt in range(2):
            try:
                prompt = f"Context (Paper Abstract): {abstract}\n\nQuestion: {question}\n\nAnswer:"
                response = client.models.generate_content(model=model, contents=prompt)
                return response.text
            except Exception as e:
                last_error = str(e)
                if "503" in last_error or "429" in last_error:
                    time.sleep(2)
                    continue
                else:
                    break
                    
    # THIS WILL NOW SHOW US THE EXACT GOOGLE ERROR
    raise Exception(f"REAL ERROR: {last_error}")