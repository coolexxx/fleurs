import streamlit as st
import random
from bs4 import BeautifulSoup
import requests
import time
import re
import base64
import json
import urllib.parse

# Set page config
st.set_page_config(layout="wide", page_title="Les Fleurs du Mal", page_icon="🌹")

# Load API keys from Streamlit secrets
DUMM_API_KEY = st.secrets["DUMM_API_KEY"]
GOOGLE_BOOKS_API_KEY = st.secrets["GOOGLE_BOOKS_API_KEY"]

def parse_gedichte(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    gedichte = []
    for row in soup.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 2:
            de_text = str(cols[0])
            fr_text = str(cols[1])
            gedichte.append((fr_text, de_text))
    return gedichte

def get_glossary(text, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system",
             "content": "Erstelle eine kurze Zusammenfassung (max. 2 Sätze) und liste dann die 5 wichtigsten oder schwierigsten Vokabeln mit knappen Erklärungen auf."},
            {"role": "user", "content": text}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        content = response.json()['choices'][0]['message']['content']
        # Füge einen sichtbaren Absatz zwischen Zusammenfassung und Glossar ein
        content = content.replace("\n\n", "\n\n<hr>\n\n", 1)
        return content
    else:
        return "Fehler bei der API-Anfrage"
    pass

def search_gedichte(query, gedichte):
    results = []
    for fr_text, de_text in gedichte:
        if query.lower() in fr_text.lower() or query.lower() in de_text.lower():
            results.append((fr_text, de_text))
    return results

def get_interpretation(text, focus, api_key):
    # Implement your get_interpretation function here
    pass

def format_gedicht(gedicht_text):
    soup = BeautifulSoup(gedicht_text, 'html.parser')
    title = soup.find('h4').text.strip() if soup.find('h4') else ''
    strophen = []
    for p in soup.find_all('p', class_='vers'):
        strophe = [line.strip() for line in p.stripped_strings]
        strophen.append(strophe)
    return title, strophen

def get_interpretation(text, focus, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"Interpretiere den folgenden Text unter besonderer Berücksichtigung von: {focus}"},
            {"role": "user", "content": text}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return "Fehler bei der API-Anfrage"
    pass

def get_related_books(query, google_api_key, gpt_api_key, gedicht_title, gedicht_text):
    base_url = "https://www.googleapis.com/books/v1/volumes"
    
    encoded_query = urllib.parse.quote(query)
    
    params = {
        "q": encoded_query,
        "key": google_api_key,
        "maxResults": 10,
        "langRestrict": "fr,de,en",
        "country": "DE"
    }
    
    try:
        st.info(f"Sending request to Google Books API with query: {encoded_query}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        st.success("Successfully received response from Google Books API")
        st.json(data)  # Display the raw API response for debugging
        
        books = []
        for item in data.get('items', []):
            volume_info = item.get('volumeInfo', {})
            title = volume_info.get('title', 'Unknown Title')
            authors = volume_info.get('authors', ['Unknown Author'])
            link = volume_info.get('infoLink', '#')
            language = volume_info.get('language', 'unknown')

            st.info(f"Processing book: {title}")

            is_baudelaire_author = any("baudelaire" in author.lower() for author in authors)
            problematic_title_keywords = [
                "les fleurs du mal",
                "gesammelte werke",
                "oeuvres complètes",
                "zweisprachige",
                "spleen et idéal"
            ]
            has_problematic_title = any(keyword in title.lower() for keyword in problematic_title_keywords)

            if not is_baudelaire_author and not has_problematic_title:
                book_info = {
                    'title': title,
                    'authors': authors,
                    'language': language
                }
                try:
                    gpt_comment = f"This book might provide interesting context for the poem '{gedicht_title}'."
                    books.append(f"[{title} von {', '.join(authors)}]({link}) - {gpt_comment}")
                    st.success(f"Added book to list: {title}")
                except Exception as e:
                    st.warning(f"Couldn't generate comment for book: {title}. Error: {str(e)}")
            else:
                st.info(f"Skipped book due to filtering: {title}")

        books.sort(key=lambda x: ('en' in x, 'de' in x, 'fr' in x))
        return books[:5]
    
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
        st.error(f"Response content: {response.text}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    
    return ["Error fetching related books"]

def main():
    st.markdown("<h1 style='text-align: center; color: #8B0000;'>Les Fleurs du Mal</h1>", unsafe_allow_html=True)

    # Load poems
    gedichte = parse_gedichte("gut.txt")

    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    query = st.text_input("Gib den Titel oder Text ein, um ein Gedicht zu finden:", key="search_input")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_button = st.button("Suchen", key="search", type="primary")
    with col2:
        random_button = st.button("Zufälliges Gedicht", key="random", type="secondary")
    st.markdown('</div>', unsafe_allow_html=True)

    def search():
        with st.spinner("Suche läuft..."):
            time.sleep(1)
            st.session_state.results = search_gedichte(query, gedichte)

    def random_poem():
        with st.spinner("Gedicht wird ausgewählt..."):
            time.sleep(1)
            st.session_state.results = [random.choice(gedichte)]

    if search_button or (query and st.session_state.search_input != st.session_state.get('last_search', '')):
        search()
        st.session_state['last_search'] = query
    if random_button:
        random_poem()

    st.markdown('<div class="content">', unsafe_allow_html=True)

    if 'results' in st.session_state and st.session_state.results:
        if len(st.session_state.results) > 1:
            options = [BeautifulSoup(fr_text, 'html.parser').find('h4').text.strip() for fr_text, _ in st.session_state.results]
            selected_gedicht = st.selectbox("Mehrere Gedichte gefunden. Bitte wählen Sie eines aus:", options)
            index = options.index(selected_gedicht)
            fr_text, de_text = st.session_state.results[index]
        else:
            fr_text, de_text = st.session_state.results[0]
        
        fr_title, fr_body = format_gedicht(fr_text)
        de_title, de_body = format_gedicht(de_text)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            display_gedicht(fr_title, fr_body, de_title, de_body)
        with col2:
            st.markdown("<h3 style='color: #8B0000;'>Infos und Glossar</h3>", unsafe_allow_html=True)
            with st.spinner("Infos und Glossar werden erstellt..."):
                glossary = get_glossary(fr_text, DUMM_API_KEY)
            st.markdown(f"<div class='vocab-box'>{glossary}</div>", unsafe_allow_html=True)
        
        # Interpretation section
        st.markdown("<h3 style='color: #8B0000;'>Interpretation</h3>", unsafe_allow_html=True)
        focus = st.text_input(
            "Worauf soll sich die Interpretation des obigen Gedichts konzentrieren?",
            key="focus_input")
        if st.button("Interpretation anzeigen", key="interpret_button") or (focus and focus != st.session_state.get('last_focus', '')):
            with st.spinner("Interpretation wird erstellt..."):
                interpretation = get_interpretation(fr_text, focus, DUMM_API_KEY)
            st.markdown(f"<div style='background-color: #FFE0E0; padding: 20px; border-radius: 10px;'>{interpretation}</div>", unsafe_allow_html=True)
            st.session_state['last_focus'] = focus

        # Related Books section
        st.markdown("<h3 style='color: #8B0000;'>Verwandte Literatur</h3>", unsafe_allow_html=True)
        if st.button("Verwandte Bücher anzeigen", key="related_books_button"):
            with st.spinner("Verwandte Literatur wird gesucht..."):
                related_books = get_related_books(f"Charles Baudelaire {fr_title}", GOOGLE_BOOKS_API_KEY, DUMM_API_KEY, fr_title, fr_text)
            for book in related_books:
                st.markdown(book, unsafe_allow_html=True)

    elif 'results' in st.session_state:
        st.write("Kein Gedicht gefunden.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #8B0000;
            color: white;
            text-align: center;
            padding: 10px 0;
            z-index: 999;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp {
            margin-bottom: 60px;
        }
        </style>
        <div class='footer'>
            © C. Baudelaire | Übers.: T. Robinson | Project Gutenberg | gpt-4o-mini | Google Books | Made with ❤ by Alex
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
