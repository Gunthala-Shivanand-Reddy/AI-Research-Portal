import arxiv
import feedparser
import os
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

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
    prompt = f"Explain this AI research paper abstract in simple, clear terms for a beginner:\n\n{abstract}"

    # PRIMARY: Groq - qwen3.8-27b (confirmed available from your account)
    groq_client = get_groq_client()
    if groq_client:
        try:
            result = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Explain research papers simply for beginners."},
                    {"role": "user", "content": prompt}
                ],
                model="qwen/qwen3.8-27b",
            )
            return result.choices[0].message.content
        except Exception:
            # Backup Groq model
            try:
                result = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant. Explain research papers simply for beginners."},
                        {"role": "user", "content": prompt}
                    ],
                    model="openai/gpt-oss-20b",
                )
                return result.choices[0].message.content
            except Exception:
                pass

    # FALLBACK: Gemini - gemini-2.5-flash (confirmed available from your account)
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception:
            # Backup Gemini model
            try:
                response = gemini_client.models.generate_content(
                    model="models/gemini-3.8-flash",
                    contents=prompt
                )
                return response.text
            except Exception:
                pass

    return "AI is temporarily unavailable. Please refresh the page."

def chat_about_paper(abstract, question):
    prompt = f"Paper Abstract: {abstract}\n\nQuestion: {question}"

    # PRIMARY: Groq - qwen3.8-27b (confirmed available from your account)
    groq_client = get_groq_client()
    if groq_client:
        try:
            result = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You answer questions about AI research papers clearly and simply."},
                    {"role": "user", "content": prompt}
                ],
                model="qwen/qwen3.8-27b",
            )
            return result.choices[0].message.content
        except Exception:
            # Backup Groq model
            try:
                result = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You answer questions about AI research papers clearly and simply."},
                        {"role": "user", "content": prompt}
                    ],
                    model="openai/gpt-oss-20b",
                )
                return result.choices[0].message.content
            except Exception:
                pass

    # FALLBACK: Gemini - gemini-2.5-flash (confirmed available from your account)
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt + "\n\nAnswer:"
            )
            return response.text
        except Exception:
            # Backup Gemini model
            try:
                response = gemini_client.models.generate_content(
                    model="models/gemini-3.8-flash",
                    contents=prompt + "\n\nAnswer:"
                )
                return response.text
            except Exception:
                pass

    return "AI is temporarily unavailable. Please try again in a moment."