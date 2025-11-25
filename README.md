# Book Recommender (Streamlit)

This is a simple book recommendation app built with Streamlit that fetches book data from the Google Books API.

Features
- Enter user preferences: emotion/mood and writer
- Queries Google Books API (no hardcoded book data)
- Attractive card-based UI with illustrative images (Unsplash) and book thumbnails
- View full feedback/mentions per-book on a details page; suggested next reads on the right

Requirements
- Python 3.10+ recommended

Setup (Windows PowerShell)

```powershell
cd "C:/Users/Vibhu/Desktop/Book"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

How it works
- `app.py` contains the Streamlit UI and calls `book_api.search_books`.
- `book_api.py` builds a query from the user inputs and requests results from Google Books API.

Notes
- Google Books API works without an API key for basic queries. For higher quota or customizations, add an API key and include `key=YOUR_KEY` in the request params.
- The app uses Unsplash to fetch illustrative images for frontend visuals (no API key required). If you want AI-generated cover images, you can add an OpenAI/DALL·E key to `.env` and I can plug that in.
- The app uses a small mapping for `emotion` -> keywords to improve results, located in `book_api.py`.
 - The app uses Unsplash to fetch an AI-style illustrative hero image for the home page and image queries for the cards (no API key required). These are decorative and vary by Unsplash results.
 - If you want true AI-generated artwork for the home hero, provide an OpenAI/DALL·E or other image API key in `.env` and I can integrate generation + caching.

Next steps you might want me to do:
- Add pagination / load-more
- Add Open Library fallback if no Google Books results
- Add caching to reduce API calls
- Package into a single executable or Docker image

