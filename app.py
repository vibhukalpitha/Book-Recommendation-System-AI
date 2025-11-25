import streamlit as st
from book_api import search_books
import book_api as _book_api
from urllib.parse import quote_plus
import requests
from io import BytesIO


# Small helper to return an Unsplash image URL for a given query (no API key required)
def unsplash_image(query: str, w: int = 800, h: int = 600) -> str:
    q = quote_plus(query or "book")
    return f"https://source.unsplash.com/{w}x{h}/?{q},book,reading"


def _rerun():
    """Compatibility helper to rerun the Streamlit script across Streamlit versions."""
    # Call experimental_rerun only if it exists (some Streamlit versions don't expose it)
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass
    # Fallback: toggle a session_state flag to force a rerun
    st.session_state['_rerun_trigger'] = not st.session_state.get('_rerun_trigger', False)


def _fetch_image_bytes(url: str, timeout: int = 4) -> BytesIO | None:
    """Try to download an image and return a BytesIO. Returns None on failure."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200 and resp.content:
            return BytesIO(resp.content)
    except Exception:
        return None
    return None

st.set_page_config(page_title="Book Recommender", layout="wide")

st.title("Book Recommendation System")
st.markdown("Enter what kind of book you want and get recommendations fetched from public book APIs.")

background_url = unsplash_image('colorful abstract gradient background', w=2400, h=1400)
input_bg = unsplash_image('colorful books background texture', w=1600, h=480)

st.markdown(
        f"""
        <style>
        :root {{--accent1: #7c3aed; --accent2: #06b6d4; --accent3: #f97316;}}
        html, body, .stApp {{height:100%;}}
        body {{
            background-image: url('{background_url}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            padding-top: 24px;
        }}
        /* soften the page container so the background shows through */
        .block-container {{
            background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
            border-radius: 12px;
            padding: 32px 40px 40px 40px;
            margin-top: 18px;
        }}

        /* Cards */
        .card {{padding:16px; border-radius:12px; box-shadow: 0 8px 24px rgba(15,23,42,0.35); background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)); margin-bottom:16px}}
        .card-title {{font-size:18px; font-weight:700; margin-bottom:6px; color: white}}
        .card-meta {{color:rgba(255,255,255,0.75); font-size:13px}}
        .small-muted {{color:rgba(255,255,255,0.75); font-size:12px}}

        /* Hero */
        .hero {{border-radius:12px; overflow:hidden; margin-bottom:20px}}
        .hero .overlay {{padding:40px; color: #ffffff; background: linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0.45));}}
        .hero h1 {{font-size:38px; margin:0 0 8px; color: #fff}}
        .hero p {{font-size:16px; margin:0; color: #f3f4f6}}

        /* Buttons */
        .stButton>button {{
            background: linear-gradient(90deg, var(--accent1), var(--accent2));
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            box-shadow: 0 6px 18px rgba(124,58,237,0.25);
        }}
        .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(124,58,237,0.32); }}

        /* Input/slider simplified look */
        .stTextInput>div>div>input, textarea {{
            background: rgba(255,255,255,0.02) !important;
            color: #fff !important;
            border-radius: 8px;
            padding: 10px;
        }}

        /* Input panel (wraps the form) */
        .input-panel {{
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 18px;
            background: linear-gradient(90deg, rgba(124,58,237,0.28), rgba(6,182,212,0.18)), url('{input_bg}');
            background-size: cover;
            background-position: center;
            background-blend-mode: overlay;
            box-shadow: 0 10px 30px rgba(2,6,23,0.22);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(255,255,255,0.07);
        }}
        .input-panel .stTextInput>div>div>input, .input-panel textarea {{
            background: linear-gradient(90deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)) !important;
            color: #0b1220 !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            padding: 12px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
        }}
        .input-panel .stSlider>div>div {{
            color: #fff;
        }}

        /* small muted text */
        .stCaption, .small-muted {{ color: rgba(255,255,255,0.75) }}

        /* make links more visible */
        a {{ color: #ffedd5; }}
        .icon {{display:inline-block; vertical-align:middle; margin-right:8px}}
        .hero .overlay .hero-icon {{width:64px; height:64px; float:left; margin-right:18px; filter: drop-shadow(0 6px 12px rgba(0,0,0,0.35));}}
        .input-label {{display:flex; align-items:center; gap:8px; font-weight:600; color:#e6eef8; margin-bottom:6px}}
        .input-label svg {{width:20px; height:20px; opacity:0.95}}
        </style>
        """,
        unsafe_allow_html=True,
)

# Hero section on home page (AI-style illustrative image)
if st.session_state.get('page', 'home') == 'home':
        hero_img = unsplash_image('artificial intelligence book reading illustration', w=1400, h=480)
        # inline SVG robot icon
        robot_svg = """<svg viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg' fill='none'><rect x='12' y='18' width='40' height='28' rx='6' fill='white' fill-opacity='0.12'/><rect x='22' y='10' width='20' height='10' rx='3' fill='white' fill-opacity='0.12'/><circle cx='28' cy='32' r='3' fill='white'/><circle cx='36' cy='32' r='3' fill='white'/><rect x='28' y='38' width='8' height='3' rx='1.5' fill='white' fill-opacity='0.12'/><rect x='30' y='6' width='4' height='6' rx='2' fill='white' fill-opacity='0.12'/></svg>"""
        st.markdown(
                f"""
                <div class="hero" style="background-image:url('{hero_img}'); background-size:cover; background-position:center;">
                    <div class="overlay">
                        <div class='hero-icon'>{robot_svg}</div>
                        <div style='overflow:hidden'>
                          <h1>Find the perfect book for your mood</h1>
                          <p>Tell me how you feel or an author you like — I'll suggest books and show what people are saying about them.</p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
        )

if 'books' not in st.session_state:
    st.session_state['books'] = None
    st.session_state['emotion'] = ""
    st.session_state['author'] = ""
    st.session_state['page'] = 'home'
    st.session_state['current_book'] = None

st.markdown("<div class='input-panel'>", unsafe_allow_html=True)
with st.form(key='pref_form'):
    col1, col2 = st.columns(2)
    with col1:
        # custom label with emoji/SVG icon + text
        st.markdown("<div class='input-label'>" + \
                    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.5' style='width:20px;height:20px'><circle cx='12' cy='8' r='1.5' fill='#fff'/><path d='M8 14c0 2 2 3 4 3s4-1 4-3' stroke='#fff' stroke-linecap='round' stroke-linejoin='round'/></svg>" + \
                    "<span>Emotion / Mood (e.g. happy, sad, adventurous)</span></div>", unsafe_allow_html=True)
        emotion = st.text_input("", value=st.session_state.get('emotion', ''), placeholder="e.g. happy, sad, adventurous")
    with col2:
        st.markdown("<div class='input-label'>" + \
                    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.5' style='width:20px;height:20px'><path d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z' fill='#fff'/><path d='M6 20c0-2 2.686-3 6-3s6 1 6 3' stroke='#fff' stroke-linecap='round' stroke-linejoin='round'/></svg>" + \
                    "<span>Writer / Author (optional)</span></div>", unsafe_allow_html=True)
        author = st.text_input("", value=st.session_state.get('author', ''), placeholder="Optional: e.g. J.K. Rowling")
        num = st.slider("Number of results", 1, 12, 6, key='num_results')

    submitted = st.form_submit_button("Get Recommendations")
    # when user submits, save inputs into session_state so a rerun keeps them
    if submitted:
        st.session_state['emotion'] = emotion
        st.session_state['author'] = author
        st.session_state['page'] = 'home'

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    with st.spinner("Searching books..."):
        # do not fetch external feedback on initial search (fetch on demand)
        books = search_books(
            emotion=st.session_state.get('emotion', ''),
            author=st.session_state.get('author', ''),
            max_results=st.session_state.get('num_results', 6),
            include_feedback=False,
        )
        # persist results so button clicks won't clear the list
        st.session_state['books'] = books

# Use persisted books if available (render regardless of current 'submitted' value)
books_to_show = st.session_state.get('books') or []
if st.session_state.get('page') == 'details' and st.session_state.get('current_book'):
    # Details page for a single book
    book = st.session_state['current_book']
    cols = st.columns([3, 1])
    with cols[0]:
        st.header(book.get('title') or 'Untitled')
        authors = ", ".join(book.get('authors') or [])
        if authors:
            st.subheader(authors)
        if book.get('publishedDate'):
            st.caption(f"Published: {book.get('publishedDate')}")
        if book.get('thumbnail'):
            tb = _fetch_image_bytes(book.get('thumbnail'))
            if tb:
                st.image(tb, width=200)
            else:
                st.image(unsplash_image(book.get('title') or 'book', w=400, h=300), width=200)

        # full description
        desc = book.get('description') or ''
        if desc:
            st.markdown("**Description**")
            st.write(desc)

        # fetch full feedback (cache for 30 minutes)
        @st.cache_data(ttl=60 * 30)
        def _fetch_full_feedback(t, a, src='reddit'):
            return _book_api.get_full_feedback(t, a, source=src, num=6)

        with st.spinner('Fetching full feedback...'):
            feedback_items = _fetch_full_feedback(book.get('title'), ", ".join(book.get('authors') or []), 'reddit')

        st.markdown('**Feedback & Mentions**')
        if not feedback_items:
            st.info('No feedback found for this book.')
        else:
            for it in feedback_items:
                t = it.get('title') or ''
                snip = it.get('snippet') or ''
                link = it.get('link') or ''
                if link:
                    st.markdown(f"- [{t}]({link})")
                else:
                    st.markdown(f"- {t}")
                if snip:
                    st.write(snip)

        if st.button('Back to results'):
            st.session_state['page'] = 'home'
            _rerun()

    with cols[1]:
        st.markdown('**Recommended next**')
        # show other recommended books from the stored results with thumbnails
        for i, b in enumerate(st.session_state.get('books') or []):
            title = b.get('title') or ''
            if title == book.get('title'):
                continue
            # layout: small thumbnail on left, button with title on right
            rcol_img, rcol_btn = st.columns([1, 5])
            thumb = b.get('thumbnail')
            with rcol_img:
                if thumb:
                    tb = _fetch_image_bytes(thumb)
                    if tb:
                        st.image(tb, width=64)
                    else:
                        st.image(unsplash_image(title or 'book', w=120, h=160), width=64)
                else:
                    st.image(unsplash_image(title or 'book', w=120, h=160), width=64)
            with rcol_btn:
                if st.button(title, key=f'suggest_{i}'):
                    st.session_state['current_book'] = b
                    st.session_state['page'] = 'details'
                    _rerun()

else:
    if not books_to_show:
        st.info("Fill the form and click 'Get Recommendations' to see recommended books.")
    else:
        # show cards in a 2-column grid for nicer layout
        row_cols = 2
        for i in range(0, len(books_to_show), row_cols):
            row = books_to_show[i : i + row_cols]
            cols = st.columns(len(row))
            for col, bidx in zip(cols, range(i, i + len(row))):
                b = books_to_show[bidx]
                with col:
                    # card container
                    st.markdown('<div class="card">', unsafe_allow_html=True)

                    # Image: prefer thumbnail, otherwise show an inline SVG placeholder
                    thumb = b.get("thumbnail")
                    img_shown = False
                    if thumb:
                        thumb_bytes = _fetch_image_bytes(thumb)
                        if thumb_bytes:
                            st.image(thumb_bytes, width=160)
                            img_shown = True

                    if not img_shown:
                        placeholder = """
                        <div style='width:100%;height:160px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:8px;margin-bottom:8px;'>
                          <svg width='64' height='64' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>
                            <rect x='2' y='4' width='20' height='16' rx='2' fill='#ffffff' fill-opacity='0.06'/>
                            <path d='M6 8h8M6 12h8M6 16h5' stroke='#ffffff' stroke-opacity='0.7' stroke-width='1.2' stroke-linecap='round' stroke-linejoin='round'/>
                          </svg>
                        </div>
                        """
                        st.markdown(placeholder, unsafe_allow_html=True)

                    # Title and meta
                    title = b.get("title") or "Untitled"
                    authors = ", ".join(b.get("authors") or [])
                    info = b.get("infoLink") or ""
                    st.markdown(f"<div class='card-title'>{title}</div>", unsafe_allow_html=True)
                    meta = []
                    if authors:
                        meta.append(f"By: {authors}")
                    if b.get("publishedDate"):
                        meta.append(f"Published: {b.get('publishedDate')}")
                    if meta:
                        st.markdown(f"<div class='card-meta'>{' • '.join(meta)}</div>", unsafe_allow_html=True)

                    # short description trimmed
                    desc = b.get("description") or ""
                    short_desc = desc.strip()
                    if len(short_desc) > 180:
                        short_desc = short_desc[:180]
                        last = short_desc.rfind(" ")
                        if last > 0:
                            short_desc = short_desc[:last]
                        short_desc = short_desc + "..."
                    if short_desc:
                        st.markdown(f"<div class='small-muted'>{short_desc}</div>", unsafe_allow_html=True)

                    if info:
                        st.markdown(f"[More details]({info})")

                    # interest / navigate to details page
                    key = f"show_fb_{bidx}"
                    if st.button("I'm interested — Show feedback", key=key):
                        st.session_state['current_book'] = b
                        st.session_state['page'] = 'details'
                        _rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

        st.success(f"Displayed {len(books_to_show)} recommendations.")
