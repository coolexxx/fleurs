import streamlit as st
import random
from bs4 import BeautifulSoup
import requests
import time
import re
import base64
import json

# Setze die Seitenkonfiguration als erste Streamlit-Anweisung
st.set_page_config(layout="wide", page_title="Les Fleurs du Mal", page_icon="🌹")

DUMM_API_KEY = st.secrets["DUMM_API_KEY"]

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
        content = content.replace("\n\n", "\n\n<hr>\n\n", 1)
        return content
    else:
        return "Fehler bei der API-Anfrage"

def search_gedichte(query, gedichte):
    results = []
    total_occurrences = 0
    for fr_text, de_text in gedichte:
        if query.lower() in fr_text.lower() or query.lower() in de_text.lower():
            results.append((fr_text, de_text))
            # Count occurrences in both French and German text
            fr_count = fr_text.lower().count(query.lower())
            de_count = de_text.lower().count(query.lower())
            total_occurrences += fr_count + de_count
    return results, total_occurrences

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

def format_gedicht(gedicht_text):
    soup = BeautifulSoup(gedicht_text, 'html.parser')
    title = soup.find('h4').text.strip() if soup.find('h4') else ''
    strophen = []
    for p in soup.find_all('p', class_='vers'):
        strophe = [line.strip() for line in p.stripped_strings]
        strophen.append(strophe)
    return title, strophen

def display_gedicht(fr_title, fr_strophen, de_title, de_strophen):
    fr_html = f"<h3 style='text-align: center; color: #8B0000; margin-bottom: 20px;'>{fr_title}</h3>"
    for strophe in fr_strophen:
        fr_html += "<p style='margin-bottom: 20px;'>"
        for line in strophe:
            fr_html += f"{line}<br>"
        fr_html += "</p>"

    de_html = f"<h3 style='text-align: center; color: #8B0000; margin-bottom: 20px;'>{de_title}</h3>"
    for strophe in de_strophen:
        de_html += "<p style='margin-bottom: 20px;'>"
        for line in strophe:
            de_html += f"{line}<br>"
        de_html += "</p>"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between;">
        <div style="width: 48%; background-color: #FFEBEB; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);">
            {fr_html}
        </div>
        <div style="width: 48%; background-color: #FFE0E0; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);">
            {de_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.markdown("""
    <style>
    .title-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .title-container img {
        width: 50px; 
        height: auto; 
        margin-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #8B0000;'>Les Fleurs du Mal</h1>", unsafe_allow_html=True)

    # Titel und Bilder
    image_path = "baud.webp"
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    st.markdown(f"""
    <div class="title-container">
        <h2 style='text-align: center; font-size: 1.5em; color: #4a4a4a;'>Entdecke die Poesie von Charles Baudelaire</h2>
        <img src="data:image/webp;base64,{encoded_string}" alt="Charles Baudelaire">
    </div>
    """, unsafe_allow_html=True)

    gedichte = parse_gedichte("gut.txt")

    st.markdown(
        '<p style="font-size: 0.7em; color: #8B0000; margin-top: 5px;">Einige Inhalte auf dieser Seite werden von einer KI verarbeitet. Bitte überprüfe wichtige Informationen immer mit zuverlässigen Quellen! Siehe hierzu bspw. auch: <a href="https://www.ku.de/die-ku/organisation/personalentwicklung-und-weiterbildung/wissenschaftliches-personal/hochschuldidaktik/ki-und-hochschullehre">KI an der KU</a> </p>',
        unsafe_allow_html=True)

    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    query = st.text_input("Gib den Titel oder Text ein, um ein Gedicht zu finden:", key="search_input")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_button = st.button("Suchen", key="search", type="primary")
    with col2:
        random_button = st.button("Zufälliges Gedicht", key="random", type="secondary")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    def search():
        with st.spinner("Suche läuft..."):
            time.sleep(1)
            results, total_occurrences = search_gedichte(query, gedichte)
            st.session_state.results = results
            if len(query.split()) == 1 and query:  # If searching for a single word
                st.info(f'Das Wort "{query}" kommt insgesamt {total_occurrences} mal vor.')

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

    if 'results' in st.session_state:
        if not st.session_state.results:
            st.write("Kein Gedicht gefunden.")
        else:
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
            © C. Baudelaire | Übers.: T. Robinson | Project Gutenberg | gpt-4o-mini | Made by Alex
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
