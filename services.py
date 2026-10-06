import arxiv
import feedparser
import os
import time
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY is missing from Render environment variables"
    return genai.Client(api_key=api_key), None

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, "GROQ_API_KEY is missing from Render environment variables"
    return Groq(api_key=api_key), None

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
    error_log = []

    # ---- STEP 1: TRY GROQ ----
    groq_client, groq_init_error = get_groq_client()
    if groq_init_error:
        error_log.append(f"Groq Init: {groq_init_error}")
    else:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Explain research papers simply for beginners."},
                    {"role": "user", "content": f"Explain this AI research paper abstract:\n\n{abstract}"}
                ],
                model="llama3-8b-8192",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            error_log.append(f"Groq API Error: {str(e)}")

    # ---- STEP 2: TRY GEMINI ----
    gemini_client, gemini_init_error = get_gemini_client()
    if gemini_init_error:
        error_log.append(f"Gemini Init: {gemini_init_error}")
    else:
        gemini_models = ['gemini-2.0-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-flash']
        for model in gemini_models:
            try:
                response = gemini_client.models.generate_content(
                    model=model,
                    contents=f"Explain this AI research paper abstract simply:\n\n{abstract}"
                )
                return response.text
            except Exception as e:
                error_log.append(f"Gemini [{model}]: {str(e)}")

    # ---- ALL FAILED: Show exact errors ----
    return "ALL AI ATTEMPTS FAILED. Here is exactly why:\n\n" + "\n\n".join(error_log)

def chat_about_paper(abstract, question):
    error_log = []

    # ---- STEP 1: TRY GROQ ----
    groq_client, groq_init_error = get_groq_client()
    if groq_init_error:
        error_log.append(f"Groq Init: {groq_init_error}")
    else:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You answer questions about AI research papers."},
                    {"role": "user", "content": f"Context: {abstract}\n\nQuestion: {question}"}
                ],
                model="llama3-8b-8192",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            error_log.append(f"Groq API Error: {str(e)}")

    # ---- STEP 2: TRY GEMINI ----
    gemini_client, gemini_init_error = get_gemini_client()
    if gemini_init_error:
        error_log.append(f"Gemini Init: {gemini_init_error}")
    else:
        gemini_models = ['gemini-2.0-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-flash']
        for model in gemini_models:
            try:
                response = gemini_client.models.generate_content(
                    model=model,
                    contents=f"Context: {abstract}\n\nQuestion: {question}\n\nAnswer:"
                )
                return response.text
            except Exception as e:
                error_log.append(f"Gemini [{model}]: {str(e)}")

    return "ALL AI ATTEMPTS FAILED. Here is exactly why:\n\n" + "\n\n".join(error_log)