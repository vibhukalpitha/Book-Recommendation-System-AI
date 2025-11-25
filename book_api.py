import os
import random
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Simple mapping from emotion -> keywords/genres to help shape queries
EMOTION_KEYWORDS = {
    "happy": ["feel-good", "humor", "optimistic", "uplifting"],
    "sad": ["melancholy", "tragic", "loss", "heartbreak"],
    "adventurous": ["adventure", "thriller", "action"],
    "romantic": ["romance", "love story", "romantic"],
    "scared": ["horror", "thriller", "ghost"],
    "curious": ["nonfiction", "science", "history", "mystery"],
    "calm": ["meditation", "mindfulness", "poetry"],
}

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
SERPAPI_SEARCH = "https://serpapi.com/search.json"
YOUTUBE_SEARCH = "https://www.googleapis.com/youtube/v3/search"
NEWSAPI_SEARCH = "https://newsapi.org/v2/everything"
REDDIT_SEARCH = "https://www.reddit.com/search.json"


def _collect_keys(prefix: str) -> List[str]:
    """Collect sequentially numbered keys from environment: PREFIX, PREFIX_1, PREFIX_2, ..."""
    keys = []
    
    for i in range(0, 10):
        name = prefix if i == 0 else f"{prefix}_{i}"
        val = os.getenv(name)
        if val:
            keys.append(val)
    return keys


def _pick_key(prefix: str) -> str:
    keys = _collect_keys(prefix)
    return random.choice(keys) if keys else ""


def build_query(emotion: str = None, author: str = None) -> str:
    """Build a Google Books API query string from emotion and author only (genre removed)."""
    parts = []
    if author:
        parts.append(f"inauthor:{author}")
    if emotion:
        kw = EMOTION_KEYWORDS.get(emotion.lower())
        if kw:
            parts.append(" ".join(kw))
        else:
            parts.append(emotion)

    if not parts:
        return ""

    return "+".join([p.replace(" ", "+") for p in parts])


def _fetch_serp_feedback(query: str, num: int = 3) -> List[Dict[str, str]]:
    key = _pick_key("SERPAPI_KEY")
    if not key:
        return []
    params = {"q": f"{query} book review", "api_key": key}
    try:
        r = requests.get(SERPAPI_SEARCH, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        results = []
        for o in data.get("organic_results", [])[:num]:
            results.append({
                "title": o.get("title"),
                "snippet": o.get("snippet") or o.get("snippet_text") or "",
                "link": o.get("link") or o.get("displayed_link") or "",
            })
        return results
    except Exception:
        return []


def _fetch_youtube_feedback(query: str, num: int = 3) -> List[Dict[str, str]]:
    key = _pick_key("YOUTUBE_API_KEY")
    if not key:
        return []
    params = {
        "part": "snippet",
        "q": f"{query} book review",
        "key": key,
        "type": "video",
        "maxResults": num,
    }
    try:
        r = requests.get(YOUTUBE_SEARCH, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        res = []
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            snip = item.get("snippet", {})
            title = snip.get("title")
            desc = snip.get("description")
            link = f"https://www.youtube.com/watch?v={vid}" if vid else ""
            res.append({"title": title, "snippet": desc, "link": link})
        return res
    except Exception:
        return []


def _fetch_news_feedback(query: str, num: int = 3) -> List[Dict[str, str]]:
    key = _pick_key("NEWS_API_KEY")
    if not key:
        return []
    params = {"q": f"{query}", "apiKey": key, "pageSize": num}
    try:
        r = requests.get(NEWSAPI_SEARCH, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        res = []
        for a in data.get("articles", [])[:num]:
            res.append({"title": a.get("title"), "snippet": a.get("description"), "link": a.get("url")})
        return res
    except Exception:
        return []


def _fetch_reddit_feedback(query: str, num: int = 3) -> List[Dict[str, str]]:
    ua = os.getenv("REDDIT_USER_AGENT", "book-recommender/0.1")
    headers = {"User-Agent": ua}
    params = {"q": f"{query} book", "limit": num, "sort": "relevance"}
    try:
        r = requests.get(REDDIT_SEARCH, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        res = []
        for child in data.get("data", {}).get("children", [])[:num]:
            d = child.get("data", {})
            res.append({
                "title": d.get("title"),
                "snippet": d.get("selftext") or "",
                "link": f"https://reddit.com{d.get('permalink')}" if d.get("permalink") else "",
            })
        return res
    except Exception:
        return []


def _trim(text: str | None, max_len: int = 180) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    # trim at last space before max_len
    cut = text[: max_len - 1]
    last_space = cut.rfind(" ")
    if last_space > 0:
        return cut[:last_space] + "..."
    return cut + "..."


def get_short_feedback(title: str, author: str = "", source: str = "reddit", num: int = 2, max_len: int = 180) -> List[Dict[str, str]]:
    """Fetch a small number of short feedback snippets for a book from one source.

    source: one of 'reddit', 'youtube', 'serp', 'news'. Falls back to reddit.
    Returns list of {'title','snippet','link'} with snippets trimmed to max_len.
    """
    query = f"{title} {author}".strip()
    src = (source or "reddit").lower()
    fetchers = {
        "reddit": _fetch_reddit_feedback,
        "youtube": _fetch_youtube_feedback,
        "serp": _fetch_serp_feedback,
        "news": _fetch_news_feedback,
    }
    fetch = fetchers.get(src) or _fetch_reddit_feedback
    items = []
    try:
        raw = fetch(query, num=num)
        for it in raw[:num]:
            items.append({
                "title": _trim(it.get("title"), max_len=80),
                "snippet": _trim(it.get("snippet"), max_len=max_len),
                "link": it.get("link") or "",
            })
    except Exception:
        return []
    return items


def get_full_feedback(title: str, author: str = "", source: str = "reddit", num: int = 3) -> List[Dict[str, str]]:
    """Fetch untrimmed/full feedback items from one source.

    source: 'reddit', 'youtube', 'serp', 'news'. Returns raw results (title, snippet, link).
    """
    query = f"{title} {author}".strip()
    src = (source or "reddit").lower()
    fetchers = {
        "reddit": _fetch_reddit_feedback,
        "youtube": _fetch_youtube_feedback,
        "serp": _fetch_serp_feedback,
        "news": _fetch_news_feedback,
    }
    fetch = fetchers.get(src) or _fetch_reddit_feedback
    try:
        raw = fetch(query, num=num)
        return raw[:num]
    except Exception:
        return []


def search_books(emotion: str = None, author: str = None, max_results: int = 6, include_feedback: bool = False) -> List[Dict[str, Any]]:
    """Search books using Google Books API and optionally fetch aggregated feedback from external APIs.

    Returns a list of dicts with keys: title, authors, description, thumbnail, infoLink, publishedDate, (optional) feedback
    """
    q = build_query(emotion, author)
    params = {
        "q": q or "",
        "maxResults": min(max(1, max_results), 40),
    }

    if q == "":
        fallback_terms = []
        if emotion:
            fallback_terms.append(emotion)
        if author:
            fallback_terms.append(f"inauthor:{author}")
        if fallback_terms:
            params["q"] = "+".join([t.replace(" ", "+") for t in fallback_terms])
        else:
            params["q"] = "bestseller"

    try:
        resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    data = resp.json()
    items = data.get("items", [])
    results: List[Dict[str, Any]] = []
    for item in items[: params["maxResults"]]:
        vol = item.get("volumeInfo", {})
        title = vol.get("title")
        authors = vol.get("authors", [])
        description = vol.get("description") or vol.get("subtitle") or ""
        image_links = vol.get("imageLinks", {})
        thumbnail = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        info_link = vol.get("infoLink")
        published_date = vol.get("publishedDate")
        book = {
            "title": title,
            "authors": authors,
            "description": description,
            "thumbnail": thumbnail,
            "infoLink": info_link,
            "publishedDate": published_date,
        }

        # optionally collect external feedback
        if include_feedback and title:
            # build a small search query using title and first author if available
            author_term = authors[0] if authors else ""
            query = f"{title} {author_term}".strip()
            try:
                serp = _fetch_serp_feedback(query, num=3)
                yt = _fetch_youtube_feedback(query, num=3)
                news = _fetch_news_feedback(query, num=3)
                reddit = _fetch_reddit_feedback(query, num=3)
                book["feedback"] = {"serp": serp, "youtube": yt, "news": news, "reddit": reddit}
            except Exception:
                book["feedback"] = {"serp": [], "youtube": [], "news": [], "reddit": []}

        results.append(book)
    return results


if __name__ == "__main__":
    # quick local test (no network validation here)
    sample = search_books(emotion="happy", author="", max_results=3, include_feedback=False)
    for b in sample:
        print(b.get("title"), b.get("authors"))
