"""
Justizfachwirt/in Einstellungstest - Professionelles Trainingssystem
Vollständige Version mit allen Testbereichen
Installation: pip install streamlit pandas numpy matplotlib plotly python-docx reportlab
Starten: streamlit run justiz_quiz.py
"""

import streamlit as st
import random
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, List, Tuple, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass
import sqlite3
import base64
from io import BytesIO
import re

# Seitenkonfiguration
st.set_page_config(
    page_title="Justiz Einstellungstest Komplett",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für professionelles Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    .correct-answer {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .incorrect-answer {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c2c7 100%);
        border: 2px solid #dc3545;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .explanation-box {
        background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
        border-left: 4px solid #0066cc;
        padding: 20px;
        margin: 15px 0;
        border-radius: 10px;
    }
    
    .stat-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .progress-ring {
        transform: rotate(-90deg);
    }
    
    .timer-warning {
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .diktat-text {
        font-size: 1.2em;
        line-height: 2;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 10px;
        font-family: 'Georgia', serif;
    }
    
    .matrix-cell {
        text-align: center;
        font-weight: bold;
        padding: 10px;
        background: white;
        border: 2px solid #dee2e6;
    }
    
    .matrix-cell-question {
        background: #ffeaa7;
        border-color: #fdcb6e;
        font-size: 1.5em;
        color: #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)

# Datenbankinitialisierung
@st.cache_resource
def init_database():
    """Initialisiert die SQLite-Datenbank für Langzeitspeicherung"""
    conn = sqlite3.connect('justiz_training.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Tabellen erstellen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            created_at TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            test_type TEXT,
            difficulty TEXT,
            score REAL,
            total_questions INTEGER,
            correct_answers INTEGER,
            avg_time REAL,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            difficulty TEXT,
            correct BOOLEAN,
            time_taken REAL,
            answered_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    return conn

# Session State Initialisierung
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_test = None
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.test_history = []
    st.session_state.current_answer = None
    st.session_state.question_start_time = None
    st.session_state.test_active = False
    st.session_state.show_explanation = False
    st.session_state.test_type = None
    st.session_state.difficulty = 'medium'
    st.session_state.db = init_database()
    st.session_state.diktat_audio = None
    st.session_state.user_stats = {
        'total_tests': 0,
        'total_questions': 0,
        'correct_answers': 0,
        'category_performance': {},
        'weak_areas': [],
        'strong_areas': []
    }

# Klasse für Rechtschreibung und Grammatik
class DeutschTest:
    """Generator für Deutsch-Aufgaben"""
    
    @staticmethod
    def generate_rechtschreibung(difficulty: str) -> Dict:
        """Generiert Rechtschreibaufgaben"""
        
        words = {
            'easy': [
                ('Rhythmus', ['Rythmus', 'Rhytmus', 'Rytmus']),
                ('Standard', ['Standart', 'Standart', 'Standarth']),
                ('Adresse', ['Addresse', 'Adrese', 'Addressse']),
                ('separat', ['seperat', 'separat', 'seperath']),
            ],
            'medium': [
                ('Parallelität', ['Paralelität', 'Paralellität', 'Paralelietät']),
                ('Portemonnaie', ['Portmonee', 'Portemonee', 'Portmoney']),
                ('Resümee', ['Resume', 'Resumee', 'Resüme']),
                ('Akquise', ['Aquise', 'Akquise', 'Acquise']),
            ],
            'hard': [
                ('Subsidiarität', ['Subsidarität', 'Subsidearität', 'Subsiediarität']),
                ('Legitimität', ['Legitimietät', 'Legitiemität', 'Legitemität']),
                ('Koryphäe', ['Koriphäe', 'Korifäe', 'Korifee']),
                ('Hämorragie', ['Hämorrhagie', 'Hämoragie', 'Hemorragie']),
            ]
        }
        
        word_list = words.get(difficulty, words['easy'])
        correct_word, wrong_options = random.choice(word_list)
        all_options = [correct_word] + wrong_options
        random.shuffle(all_options)
        
        return {
            'type': 'rechtschreibung',
            'question': 'Welche Schreibweise ist korrekt?',
            'options': all_options,
            'answer': all_options.index(correct_word),
            'explanation': f'Die korrekte Schreibweise ist: {correct_word}'
        }
    
    @staticmethod
    def generate_kommasetzung(difficulty: str) -> Dict:
        """Generiert Kommasetzungsaufgaben"""
        
        sentences = {
            'easy': [
                {
                    'text': 'Der Angeklagte[K1] der seit Monaten in Haft sitzt[K2] wartet auf sein Urteil.',
                    'correct_commas': [True, True],
                    'explanation': 'Relativsatz wird durch Kommas eingeschlossen.'
                },
                {
                    'text': 'Sie können kommen[K1] oder wir kommen zu Ihnen.',
                    'correct_commas': [True],
                    'explanation': 'Vor "oder" bei vollständigen Hauptsätzen steht ein Komma.'
                }
            ],
            'medium': [
                {
                    'text': 'Der Richter betonte[K1] dass alle Zeugen[K2] die geladen wurden[K3] erscheinen müssen.',
                    'correct_commas': [True, True, True],
                    'explanation': 'dass-Satz und Relativsatz benötigen Kommas.'
                }
            ],
            'hard': [
                {
                    'text': 'Ohne die Akten studiert zu haben[K1] kann niemand[K2] und sei er noch so erfahren[K3] ein gerechtes Urteil fällen.',
                    'correct_commas': [True, True, True],
                    'explanation': 'Infinitivgruppe und eingeschobener Konzessivsatz.'
                }
            ]
        }
        
        sentence_data = random.choice(sentences.get(difficulty, sentences['easy']))
        
        # Erstelle Satz mit Komma-Markierungen
        display_text = sentence_data['text']
        for i, needs_comma in enumerate(sentence_data['correct_commas'], 1):
            marker = f'[K{i}]'
            if needs_comma:
                display_text = display_text.replace(marker, ' ___')
        
        return {
            'type': 'kommasetzung',
            'question': 'Wo müssen Kommas gesetzt werden?',
            'text': display_text,
            'correct_positions': sentence_data['correct_commas'],
            'explanation': sentence_data['explanation']
        }
    
    @staticmethod
    def generate_diktat(difficulty: str) -> Dict:
        """Generiert Diktat-Texte"""
        
        diktate = {
            'easy': """
            Die Digitalisierung der Justiz schreitet kontinuierlich voran. 
            Elektronische Akten erleichtern die tägliche Arbeit erheblich. 
            Dokumente können schneller bearbeitet und archiviert werden.
            """,
            'medium': """
            Im Rahmen der Justizmodernisierung wurden verschiedene Maßnahmen implementiert.
            Die Effizienzsteigerung durch digitale Prozesse ist bemerkenswert.
            Gleichzeitig müssen Datenschutzaspekte sorgfältig berücksichtigt werden.
            Die Balance zwischen Modernisierung und Rechtssicherheit bleibt essentiell.
            """,
            'hard': """
            Die Subsidiarität des Verfassungsbeschwerdeverfahrens manifestiert sich 
            in der Notwendigkeit der Rechtswegerschöpfung. Präjudizielle Fragestellungen 
            erfordern häufig eine Vorlage an übergeordnete Instanzen. Die Kohärenz 
            der Rechtsprechung verschiedener Jurisdiktionen bleibt dabei von 
            eminenter Bedeutung für die Rechtseinheitlichkeit.
            """
        }
        
        text = diktate.get(difficulty, diktate['easy']).strip()
        
        # Erstelle Lückentext (entferne zufällige schwierige Wörter)
        words = text.split()
        difficult_words = [w for w in words if len(w) > 7 and not w[0].isupper()]
        gaps = random.sample(difficult_words, min(5, len(difficult_words)))
        
        gap_text = text
        for gap in gaps:
            gap_text = gap_text.replace(gap, '_' * len(gap), 1)
        
        return {
            'type': 'diktat',
            'question': 'Füllen Sie die Lücken im Text:',
            'full_text': text,
            'gap_text': gap_text,
            'missing_words': gaps,
            'explanation': 'Achten Sie auf Rechtschreibung und Groß-/Kleinschreibung.'
        }

# Klasse für Mathematik-Aufgaben
class MathematikTest:
    """Generator für Mathematik-Aufgaben"""
    
    @staticmethod
    def generate_dreisatz(difficulty: str) -> Dict:
        """Generiert Dreisatzaufgaben"""
        
        scenarios = {
            'easy': [
                {
                    'context': 'Aktenbearbeitung',
                    'given': '5 Mitarbeiter bearbeiten 120 Akten in 3 Tagen.',
                    'question': 'Wie viele Akten bearbeiten 8 Mitarbeiter in 3 Tagen?',
                    'calculation': lambda: (120 / 5) * 8,
                    'explanation': 'Proportionaler Dreisatz: 120/5 × 8 = 192 Akten'
                }
            ],
            'medium': [
                {
                    'context': 'Gerichtskosten',
                    'given': '6 Verhandlungstage kosten 4.800 €.',
                    'question': 'Wie viel kosten 15 Verhandlungstage?',
                    'calculation': lambda: (4800 / 6) * 15,
                    'explanation': 'Proportional: 4800/6 × 15 = 12.000 €'
                }
            ],
            'hard': [
                {
                    'context': 'Arbeitszeit',
                    'given': '4 Sachbearbeiter benötigen 15 Tage für eine Aufgabe.',
                    'question': 'Wie lange brauchen 6 Sachbearbeiter?',
                    'calculation': lambda: (4 * 15) / 6,
                    'explanation': 'Antiproportional: (4 × 15) / 6 = 10 Tage'
                }
            ]
        }
        
        scenario = random.choice(scenarios.get(difficulty, scenarios['easy']))
        answer = scenario['calculation']()
        
        return {
            'type': 'dreisatz',
            'context': scenario['context'],
            'given': scenario['given'],
            'question': scenario['question'],
            'answer': answer,
            'explanation': scenario['explanation']
        }
    
    @staticmethod
    def generate_prozentrechnung(difficulty: str) -> Dict:
        """Generiert Prozentrechenaufgaben"""
        
        if difficulty == 'easy':
            base = random.randint(100, 500) * 10
            percent = random.choice([10, 20, 25, 50])
            answer = base * (percent / 100)
            question = f"Berechnen Sie {percent}% von {base} €"
            explanation = f"{base} × {percent}/100 = {answer} €"
            
        elif difficulty == 'medium':
            total = random.randint(150, 300)
            success = random.randint(100, total - 20)
            percent = (success / total) * 100
            question = f"Von {total} Anträgen wurden {success} bewilligt. Wie viel Prozent?"
            answer = round(percent, 1)
            explanation = f"{success}/{total} × 100 = {answer}%"
            
        else:  # hard
            new_value = random.randint(2000, 3000)
            increase = random.randint(2, 8)
            old_value = new_value / (1 + increase/100)
            question = f"Nach {increase}% Erhöhung beträgt das Gehalt {new_value} €. Wie hoch war es vorher?"
            answer = round(old_value, 2)
            explanation = f"{new_value} / 1.{increase:02d} = {answer} €"
        
        return {
            'type': 'prozent',
            'question': question,
            'answer': answer,
            'explanation': explanation
        }
    
    @staticmethod
    def generate_zeitrechnung(difficulty: str) -> Dict:
        """Generiert Zeitrechnungsaufgaben (wichtig für Fristen!)"""
        
        from datetime import datetime, timedelta
        
        if difficulty == 'easy':
            start_date = datetime(2025, 3, 15)
            days = 30
            end_date = start_date + timedelta(days=days)
            question = f"Eine Monatsfrist beginnt am 15.03.2025. Wann endet sie?"
            answer = end_date.strftime("%d.%m.%Y")
            explanation = "Monatsfrist: gleicher Tag im Folgemonat"
            
        elif difficulty == 'medium':
            start_date = datetime(2025, 1, 31)
            # Februar hat nur 28 Tage
            end_date = datetime(2025, 2, 28)
            question = f"Eine Monatsfrist beginnt am 31.01.2025. Wann endet sie?"
            answer = end_date.strftime("%d.%m.%Y")
            explanation = "Bei Monatsfrist: Wenn Tag nicht existiert, letzter Tag des Monats"
            
        else:  # hard
            # Berechne Werktage
            start_date = datetime(2025, 3, 14)  # Freitag
            workdays = 5
            current = start_date
            days_added = 0
            while days_added < workdays:
                current += timedelta(days=1)
                if current.weekday() < 5:  # Montag = 0, Freitag = 4
                    days_added += 1
            question = f"Eine 5-Werktage-Frist beginnt am Freitag, 14.03.2025. Wann endet sie?"
            answer = current.strftime("%d.%m.%Y")
            explanation = "Werktage: Sa/So zählen nicht mit"
        
        return {
            'type': 'zeitrechnung',
            'question': question,
            'answer': answer,
            'explanation': explanation
        }

# Klasse für Textverständnis
class TextverstaendnisTest:
    """Generator für Textverständnis-Aufgaben"""
    
    @staticmethod
    def generate_text_comprehension(difficulty: str) -> Dict:
        """Generiert Textverständnisaufgaben"""
        
        texts = {
            'easy': {
                'text': """
                Das Amtsgericht ist in Deutschland das Gericht der niedrigsten Stufe der 
                ordentlichen Gerichtsbarkeit. Es ist zuständig für Zivilsachen mit einem 
                Streitwert bis zu 5.000 Euro sowie für die meisten Familiensachen. 
                Im Strafrecht verhandelt das Amtsgericht Vergehen mit einer zu erwartenden 
                Freiheitsstrafe von bis zu vier Jahren. Für schwerere Delikte ist das 
                Landgericht zuständig.
                """,
                'questions': [
                    {
                        'q': 'Bis zu welchem Streitwert ist das Amtsgericht in Zivilsachen zuständig?',
                        'options': ['3.000 €', '5.000 €', '10.000 €', '15.000 €'],
                        'answer': 1
                    },
                    {
                        'q': 'Welches Gericht ist für schwerere Straftaten zuständig?',
                        'options': ['Oberlandesgericht', 'Landgericht', 'Bundesgerichtshof', 'Amtsgericht'],
                        'answer': 1
                    }
                ]
            },
            'medium': {
                'text': """
                Die Rechtsmittel im deutschen Zivilprozess sind hierarchisch gegliedert. 
                Gegen erstinstanzliche Urteile des Amtsgerichts ist bei einem Beschwerdewert 
                über 600 Euro die Berufung zum Landgericht möglich. Gegen Berufungsurteile 
                kann unter bestimmten Voraussetzungen Revision beim Bundesgerichtshof 
                eingelegt werden. Die Revision prüft jedoch nur Rechtsfehler, keine 
                Tatsachenfeststellungen. Neben diesen ordentlichen Rechtsmitteln existieren 
                auch außerordentliche wie die Nichtigkeitsklage.
                """,
                'questions': [
                    {
                        'q': 'Ab welchem Beschwerdewert ist eine Berufung gegen Amtsgerichtsurteile möglich?',
                        'options': ['300 €', '500 €', '600 €', '1.000 €'],
                        'answer': 2
                    },
                    {
                        'q': 'Was prüft die Revision?',
                        'options': ['Nur Tatsachen', 'Nur Rechtsfehler', 'Tatsachen und Recht', 'Nur Verfahrensfehler'],
                        'answer': 1
                    }
                ]
            },
            'hard': {
                'text': """
                Das Prinzip der Gewaltenteilung manifestiert sich in der Unabhängigkeit 
                der Judikative. Richter sind gemäß Art. 97 GG sachlich und persönlich 
                unabhängig und nur dem Gesetz unterworfen. Die richterliche Unabhängigkeit 
                wird durch verschiedene Garantien abgesichert: Richter auf Lebenszeit können 
                nur durch richterliche Entscheidung und nur aus gesetzlich bestimmten Gründen 
                vor Erreichen der Altersgrenze entlassen werden. Die Besoldung ist gesetzlich 
                geregelt und der Einflussnahme der Exekutive entzogen. Diese strukturellen 
                Sicherungen gewährleisten die Neutralität der Rechtsprechung und sind 
                essentieller Bestandteil des Rechtsstaatsprinzips.
                """,
                'questions': [
                    {
                        'q': 'Welcher Grundgesetzartikel regelt die richterliche Unabhängigkeit?',
                        'options': ['Art. 92 GG', 'Art. 95 GG', 'Art. 97 GG', 'Art. 101 GG'],
                        'answer': 2
                    },
                    {
                        'q': 'Wodurch wird die Unabhängigkeit der Richter NICHT gesichert?',
                        'options': [
                            'Ernennung auf Lebenszeit',
                            'Gesetzliche Besoldungsregelung',
                            'Weisungsgebundenheit gegenüber Vorgesetzten',
                            'Schutz vor willkürlicher Entlassung'
                        ],
                        'answer': 2
                    }
                ]
            }
        }
        
        text_data = texts.get(difficulty, texts['easy'])
        question = random.choice(text_data['questions'])
        
        return {
            'type': 'textverstaendnis',
            'text': text_data['text'].strip(),
            'question': question['q'],
            'options': question['options'],
            'answer': question['answer'],
            'explanation': 'Die Antwort ergibt sich direkt aus dem Text.'
        }

# Klasse für Allgemeinwissen
class AllgemeinwissenTest:
    """Generator für Allgemeinwissen-Fragen"""
    
    @staticmethod
    def generate_politik(difficulty: str) -> Dict:
        """Politische Bildung und Staatskunde"""
        
        questions = {
            'easy': [
                {
                    'q': 'Wer ist das Staatsoberhaupt der Bundesrepublik Deutschland?',
                    'options': ['Bundeskanzler', 'Bundespräsident', 'Bundestagspräsident', 'Ministerpräsident'],
                    'answer': 1,
                    'explanation': 'Der Bundespräsident ist das Staatsoberhaupt, der Bundeskanzler ist Regierungschef.'
                },
                {
                    'q': 'Wie lange dauert eine Legislaturperiode des Bundestages?',
                    'options': ['3 Jahre', '4 Jahre', '5 Jahre', '6 Jahre'],
                    'answer': 1,
                    'explanation': 'Die Legislaturperiode beträgt 4 Jahre.'
                }
            ],
            'medium': [
                {
                    'q': 'Welches Organ wählt den Bundeskanzler?',
                    'options': ['Bundesrat', 'Bundestag', 'Bundesversammlung', 'Volk direkt'],
                    'answer': 1,
                    'explanation': 'Der Bundestag wählt den Bundeskanzler auf Vorschlag des Bundespräsidenten.'
                },
                {
                    'q': 'Wie viele Richter hat das Bundesverfassungsgericht?',
                    'options': ['8', '12', '16', '20'],
                    'answer': 2,
                    'explanation': 'Das BVerfG hat 16 Richter, je 8 in zwei Senaten.'
                }
            ],
            'hard': [
                {
                    'q': 'Welche Mehrheit benötigt eine Grundgesetzänderung?',
                    'options': ['Einfache Mehrheit', 'Absolute Mehrheit', '2/3 in Bundestag und Bundesrat', '3/4 in Bundestag und Bundesrat'],
                    'answer': 2,
                    'explanation': 'Art. 79 Abs. 2 GG: 2/3 der Mitglieder des Bundestages und 2/3 der Stimmen des Bundesrates.'
                }
            ]
        }
        
        q_data = random.choice(questions.get(difficulty, questions['easy']))
        
        return {
            'type': 'politik',
            'question': q_data['q'],
            'options': q_data['options'],
            'answer': q_data['answer'],
            'explanation': q_data['explanation']
        }
    
    @staticmethod
    def generate_recht(difficulty: str) -> Dict:
        """Rechtskunde-Fragen"""
        
        questions = {
            'easy': [
                {
                    'q': 'Ab welchem Alter ist man in Deutschland voll geschäftsfähig?',
                    'options': ['14 Jahre', '16 Jahre', '18 Jahre', '21 Jahre'],
                    'answer': 2,
                    'explanation': 'Mit 18 Jahren tritt die volle Geschäftsfähigkeit ein (§ 2 BGB).'
                }
            ],
            'medium': [
                {
                    'q': 'Welche Verjährungsfrist gilt für die meisten zivilrechtlichen Ansprüche?',
                    'options': ['1 Jahr', '3 Jahre', '5 Jahre', '10 Jahre'],
                    'answer': 1,
                    'explanation': 'Die regelmäßige Verjährungsfrist beträgt 3 Jahre (§ 195 BGB).'
                }
            ],
            'hard': [
                {
                    'q': 'Was bedeutet "ne bis in idem"?',
                    'options': [
                        'Keine Strafe ohne Gesetz',
                        'Nicht zweimal in derselben Sache',
                        'Im Zweifel für den Angeklagten',
                        'Gleichheit vor dem Gesetz'
                    ],
                    'answer': 1,
                    'explanation': 'Verbot der Doppelbestrafung - niemand darf wegen derselben Tat zweimal bestraft werden.'
                }
            ]
        }
        
        q_data = random.choice(questions.get(difficulty, questions['easy']))
        
        return {
            'type': 'recht',
            'question': q_data['q'],
            'options': q_data['options'],
            'answer': q_data['answer'],
            'explanation': q_data['explanation']
        }
    
    @staticmethod
    def generate_hessen(difficulty: str) -> Dict:
        """Hessen-spezifische Fragen"""
        
        questions = {
            'easy': [
                {
                    'q': 'Was ist die Landeshauptstadt von Hessen?',
                    'options': ['Frankfurt', 'Wiesbaden', 'Darmstadt', 'Kassel'],
                    'answer': 1,
                    'explanation': 'Wiesbaden ist die Landeshauptstadt, Frankfurt die größte Stadt.'
                }
            ],
            'medium': [
                {
                    'q': 'Wo hat das Oberlandesgericht Hessen seinen Sitz?',
                    'options': ['Wiesbaden', 'Darmstadt', 'Frankfurt am Main', 'Kassel'],
                    'answer': 2,
                    'explanation': 'Das OLG Frankfurt am Main befindet sich in der Zeil 42.'
                }
            ],
            'hard': [
                {
                    'q': 'Wie viele Amtsgerichte gibt es in Hessen?',
                    'options': ['28', '34', '40', '46'],
                    'answer': 2,
                    'explanation': 'In Hessen gibt es 40 Amtsgerichte.'
                }
            ]
        }
        
        q_data = random.choice(questions.get(difficulty, questions['easy']))
        
        return {
            'type': 'hessen',
            'question': q_data['q'],
            'options': q_data['options'],
            'answer': q_data['answer'],
            'explanation': q_data['explanation']
        }

# Klasse für Konzentration und Merkfähigkeit
class KonzentrationsTest:
    """Generator für Konzentrations- und Merkfähigkeitsaufgaben"""
    
    @staticmethod
    def generate_merkfaehigkeit(difficulty: str) -> Dict:
        """Generiert Merkfähigkeitsaufgaben"""
        
        if difficulty == 'easy':
            # Zahlenfolge merken
            length = 5
            numbers = [random.randint(1, 9) for _ in range(length)]
            
            return {
                'type': 'merkfaehigkeit_zahlen',
                'instruction': f'Merken Sie sich diese Zahlenfolge (10 Sekunden): {" ".join(map(str, numbers))}',
                'question': 'Geben Sie die Zahlenfolge ein:',
                'answer': ''.join(map(str, numbers)),
                'display_time': 10,
                'explanation': 'Merkfähigkeit für Zahlen ist wichtig für Aktenzeichen und Telefonnummern.'
            }
            
        elif difficulty == 'medium':
            # Personendaten merken
            personen = []
            vornamen = ['Anna', 'Peter', 'Maria', 'Thomas', 'Lisa']
            nachnamen = ['Schmidt', 'Müller', 'Weber', 'Fischer', 'Meyer']
            abteilungen = ['Strafrecht', 'Zivilrecht', 'Familienrecht', 'Verwaltung', 'Vollstreckung']
            
            for i in range(3):
                person = {
                    'name': f"{random.choice(vornamen)} {random.choice(nachnamen)}",
                    'abteilung': random.choice(abteilungen),
                    'zimmer': random.randint(100, 399)
                }
                personen.append(person)
            
            return {
                'type': 'merkfaehigkeit_personen',
                'instruction': 'Merken Sie sich diese Personendaten (20 Sekunden):',
                'data': personen,
                'question': f'In welcher Abteilung arbeitet {personen[1]["name"]}?',
                'answer': personen[1]['abteilung'],
                'display_time': 20,
                'explanation': 'Im Berufsalltag müssen Sie sich viele Personen und deren Zuständigkeiten merken.'
            }
            
        else:  # hard
            # Komplexe Aktenzeichen
            aktenzeichen = []
            for _ in range(5):
                az = f"{random.randint(1,30)} {'O' if random.random() > 0.5 else 'C'} {random.randint(100,999)}/{random.randint(20,24)}"
                aktenzeichen.append(az)
            
            return {
                'type': 'merkfaehigkeit_akten',
                'instruction': 'Merken Sie sich diese Aktenzeichen (30 Sekunden):',
                'data': aktenzeichen,
                'question': 'Welches war das dritte Aktenzeichen?',
                'answer': aktenzeichen[2],
                'display_time': 30,
                'explanation': 'Aktenzeichen korrekt zu merken ist essentiell in der Justiz.'
            }
    
    @staticmethod
    def generate_konzentration(difficulty: str) -> Dict:
        """Generiert Konzentrationsaufgaben"""
        
        if difficulty == 'easy':
            # Buchstaben zählen
            text = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=50))
            target_letter = random.choice('aeiou')
            count = text.count(target_letter)
            
            return {
                'type': 'konzentration_zaehlen',
                'instruction': f'Zählen Sie alle "{target_letter}" im folgenden Text:',
                'text': text,
                'answer': count,
                'explanation': f'Der Buchstabe "{target_letter}" kommt {count} mal vor.'
            }
            
        elif difficulty == 'medium':
            # Fehler in ähnlichen Texten finden
            original = "Az.: 23 O 456/24, Kläger: Schmidt, Beklagter: Müller, Streitwert: 5.000 €"
            modified = original.replace('456', '465').replace('Schmidt', 'Schmitt')
            
            return {
                'type': 'konzentration_fehler',
                'instruction': 'Finden Sie die Unterschiede zwischen den Texten:',
                'text1': original,
                'text2': modified,
                'answer': 2,
                'differences': ['456 → 465', 'Schmidt → Schmitt'],
                'explanation': 'Genauigkeit beim Vergleichen von Dokumenten ist wichtig.'
            }
            
        else:  # hard
            # Komplexe Sortieraufgabe
            items = []
            for _ in range(8):
                items.append({
                    'az': f"{random.randint(1,30)} C {random.randint(100,999)}/{random.randint(22,24)}",
                    'datum': f"{random.randint(1,28)}.{random.randint(1,12)}.{random.randint(2022,2024)}"
                })
            
            return {
                'type': 'konzentration_sortieren',
                'instruction': 'Sortieren Sie die Akten nach Datum (älteste zuerst):',
                'items': items,
                'explanation': 'Akten chronologisch zu sortieren ist eine häufige Aufgabe.'
            }

# Klasse für Logik und IQ mit erweiterten geometrischen Formen
class LogikTest:
    """Generator für erweiterte Logik- und IQ-Aufgaben mit geometrischen Formen"""
    
    @staticmethod
    def generate_zahlenreihe(difficulty: str) -> Dict:
        """Erweiterte Zahlenreihen"""
        
        patterns = {
            'easy': [
                ('arithmetic', lambda i: 2 + i * 3, 'Arithmetische Folge: +3'),
                ('geometric', lambda i: 2 * (2**i), 'Geometrische Folge: ×2'),
                ('square', lambda i: (i+1)**2, 'Quadratzahlen'),
            ],
            'medium': [
                ('fibonacci', None, 'Fibonacci-Folge'),
                ('prime', None, 'Primzahlen'),
                ('factorial', lambda i: 1 if i == 0 else i * patterns['medium'][2][1](i-1) if patterns['medium'][2][1] else 1, 'Fakultäten'),
            ],
            'hard': [
                ('mixed', None, 'Alternierende Operationen'),
                ('recursive', None, 'Rekursive Formel: a(n) = a(n-1) + a(n-2) + n'),
                ('modular', None, 'Modulo-Arithmetik'),
            ],
            'expert': [
                ('catalan', None, 'Catalan-Zahlen'),
                ('tribonacci', None, 'Tribonacci-Folge'),
                ('lucas', None, 'Lucas-Zahlen'),
            ]
        }
        
        pattern_type, func, explanation = random.choice(patterns.get(difficulty, patterns['easy']))
        
        # Generiere spezifische Sequenzen
        if pattern_type == 'fibonacci':
            a, b = random.randint(1, 3), random.randint(1, 3)
            sequence = [a, b]
            for _ in range(4):
                sequence.append(sequence[-1] + sequence[-2])
        elif pattern_type == 'prime':
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]
            start = random.randint(0, 10)
            sequence = primes[start:start+6]
        elif pattern_type == 'mixed':
            ops = [('+', random.randint(3, 7)), ('*', 2)]
            start = random.randint(2, 5)
            sequence = [start]
            for i in range(5):
                op, val = ops[i % 2]
                if op == '+':
                    sequence.append(sequence[-1] + val)
                else:
                    sequence.append(sequence[-1] * val)
            explanation = f"Abwechselnd +{ops[0][1]} und ×{ops[1][1]}"
        elif pattern_type == 'catalan':
            def catalan(n):
                if n <= 1:
                    return 1
                res = 0
                for i in range(n):
                    res += catalan(i) * catalan(n-1-i)
                return res
            sequence = [catalan(i) for i in range(6)]
            explanation = "Catalan-Zahlen: C(n) = Σ C(i)×C(n-1-i)"
        elif pattern_type == 'tribonacci':
            sequence = [0, 1, 1]
            for _ in range(3):
                sequence.append(sum(sequence[-3:]))
            explanation = "Tribonacci: Summe der letzten drei Zahlen"
        elif func:
            sequence = [func(i) for i in range(6)]
        else:
            # Fallback
            d = random.randint(2, 8)
            start = random.randint(1, 10)
            sequence = [start + i*d for i in range(6)]
            explanation = f"Addition von {d}"
        
        return {
            'type': 'zahlenreihe',
            'sequence': sequence[:-1],
            'answer': sequence[-1],
            'explanation': explanation,
            'question': 'Setzen Sie die Zahlenreihe fort:'
        }
    
    @staticmethod
    def generate_geometric_pattern(difficulty: str) -> Dict:
        """Generiert geometrische Musterfolgen"""
        
        # Definiere Grundformen mit Unicode-Symbolen
        shapes = {
            'basic': ['○', '●', '□', '■', '△', '▲', '◇', '◆'],
            'extended': ['☆', '★', '♡', '♥', '⬟', '⬢', '▽', '▼'],
            'complex': ['⊕', '⊗', '⊙', '⊚', '⬡', '⬢', '⎔', '◈']
        }
        
        if difficulty == 'easy':
            # Einfache Rotation
            pattern_shapes = random.sample(shapes['basic'], 3)
            sequence = []
            for i in range(5):
                sequence.append(pattern_shapes[i % 3])
            answer = pattern_shapes[5 % 3]
            explanation = "Die Formen wiederholen sich in einem 3er-Zyklus"
            
        elif difficulty == 'medium':
            # Kombination von Form und Füllung
            base_shapes = ['○', '□', '△']
            filled_shapes = ['●', '■', '▲']
            sequence = []
            for i in range(5):
                if i % 2 == 0:
                    sequence.append(base_shapes[i // 2 % 3])
                else:
                    sequence.append(filled_shapes[i // 2 % 3])
            if 5 % 2 == 0:
                answer = base_shapes[5 // 2 % 3]
            else:
                answer = filled_shapes[5 // 2 % 3]
            explanation = "Abwechselnd ungefüllte und gefüllte Formen in Reihenfolge"
            
        elif difficulty == 'hard':
            # Komplexe Transformation
            transformations = [
                ('rotate', 90),  # Rotation
                ('scale', 1.5),  # Größenänderung
                ('fill', True),  # Füllung
            ]
            base = random.choice(shapes['basic'][:4])
            sequence = [base]
            
            # Erstelle eine komplexe Regel
            for i in range(1, 6):
                if i == 1:
                    sequence.append('→' + base)  # Rotation
                elif i == 2:
                    sequence.append('↑' + base)  # Größer
                elif i == 3:
                    filled = '●' if base == '○' else '■' if base == '□' else '▲'
                    sequence.append(filled)  # Gefüllt
                elif i == 4:
                    sequence.append('↓' + base)  # Kleiner
                else:
                    sequence.append('←' + base)  # Rotation zurück
            
            answer = sequence[5]
            explanation = "Transformation: Rotation → Vergrößerung → Füllung → Verkleinerung → Rotation"
            
        else:  # expert
            # Mehrere gleichzeitige Regeln
            sequence = []
            for i in range(5):
                shape_idx = (i * 2) % 4
                rotation = (i * 45) % 360
                size = 1 + (i % 3) * 0.5
                
                # Vereinfachte Darstellung für Text
                base_shape = shapes['complex'][shape_idx]
                modifier = '↻' if rotation > 0 else ''
                size_mod = '⁺' if size > 1 else ''
                
                sequence.append(modifier + base_shape + size_mod)
            
            # Berechne nächstes Element
            i = 5
            shape_idx = (i * 2) % 4
            answer = shapes['complex'][shape_idx]
            explanation = "Multiple Transformationen: Form-Index × 2, Rotation +45°, Größe zyklisch"
        
        return {
            'type': 'geometric_pattern',
            'sequence': sequence[:5],
            'answer': answer,
            'options': random.sample(shapes['basic'] + shapes['extended'], 4) if answer not in shapes['basic'] + shapes['extended'] else None,
            'explanation': explanation,
            'question': 'Welche Form folgt in der geometrischen Reihe?'
        }
    
    @staticmethod
    def generate_spatial_rotation(difficulty: str) -> Dict:
        """Generiert Aufgaben zur räumlichen Rotation"""
        
        # 3D-Objekt Beschreibungen (vereinfacht für Text-Darstellung)
        objects = {
            'easy': {
                'description': 'L-förmiger Block',
                'views': {
                    'front': '┌─┐\n│ │\n└ └',
                    'right': '┌┐\n││\n└┘',
                    'top': '┌──┐\n└┐ │\n └─┘',
                    'rotated_90': '┌┐\n│└┐\n└─┘'
                }
            },
            'medium': {
                'description': 'T-förmiger Block',
                'views': {
                    'front': '┌─┬─┐\n  │  \n  └  ',
                    'right': ' ┌┐\n ││\n └┘',
                    'top': '┌─┬─┐\n│ │ │\n└─┴─┘',
                    'rotated_180': '  ┌  \n  │  \n└─┴─┘'
                }
            },
            'hard': {
                'description': 'Komplexer 3D-Block mit Aussparung',
                'views': {
                    'front': '┌──┐\n│╳ │\n└──┘',
                    'right': '┌─┐\n│ │\n└─┘',
                    'top': '┌──┐\n│  │\n└──┘',
                    'rotated_90_x': '┌──┐\n│  │\n└╳─┘'
                }
            }
        }
        
        obj_data = objects.get(difficulty, objects['easy'])
        
        # Wähle zufällige Ansichten für die Frage
        views_list = list(obj_data['views'].keys())
        given_view = random.choice(views_list[:3])  # front, right, or top
        target_view = random.choice(views_list)
        
        return {
            'type': 'spatial_rotation',
            'object': obj_data['description'],
            'given_view': given_view,
            'given_image': obj_data['views'][given_view],
            'question': f"Wie sieht das Objekt aus der {target_view}-Ansicht aus?",
            'answer': obj_data['views'][target_view],
            'options': list(obj_data['views'].values()),
            'explanation': f"Bei räumlicher Rotation muss man sich das Objekt mental drehen. {given_view} → {target_view}"
        }
    
    @staticmethod
    def generate_matrix_geometric(difficulty: str) -> Dict:
        """Generiert Matrizen mit geometrischen Formen"""
        
        # Geometrische Formen für Matrizen
        shapes = ['○', '□', '△', '◇', '★', '●', '■', '▲', '◆']
        
        if difficulty == 'easy':
            # Einfaches Muster: Jede Zeile und Spalte enthält jede Form genau einmal
            matrix_size = 3
            used_shapes = shapes[:matrix_size]
            
            # Erstelle Latin Square
            matrix = []
            for i in range(matrix_size):
                row = []
                for j in range(matrix_size):
                    idx = (i + j) % matrix_size
                    row.append(used_shapes[idx])
                matrix.append(row)
            
            # Verstecke letztes Element
            answer = matrix[2][2]
            matrix[2][2] = '?'
            explanation = "Jede Form erscheint in jeder Zeile und Spalte genau einmal (Latin Square)"
            
        elif difficulty == 'medium':
            # Transformation in Zeilen und Spalten
            matrix = []
            transformations = {
                '○': '●',  # ungefüllt → gefüllt
                '□': '■',
                '△': '▲',
                '●': '○',  # gefüllt → ungefüllt
                '■': '□',
                '▲': '△'
            }
            
            # Erste Zeile
            first_row = ['○', '□', '△']
            matrix.append(first_row)
            
            # Zweite Zeile (gefüllt)
            second_row = [transformations[s] for s in first_row]
            matrix.append(second_row)
            
            # Dritte Zeile (wieder ungefüllt)
            third_row = [transformations[s] for s in second_row]
            matrix.append(third_row)
            
            answer = third_row[2]
            matrix[2][2] = '?'
            explanation = "Zeilen alternieren zwischen ungefüllten und gefüllten Formen"
            
        elif difficulty == 'hard':
            # Komplexe Regel: Überlagerung/Kombination
            matrix = []
            
            # Definiere Kombinationsregeln
            def combine_shapes(s1, s2):
                if s1 == '○' and s2 == '○':
                    return '●'
                elif s1 == '□' and s2 == '□':
                    return '■'
                elif s1 == '○' and s2 == '□':
                    return '◇'
                elif s1 == '□' and s2 == '○':
                    return '◇'
                elif s1 == '△' and s2 == '△':
                    return '▲'
                else:
                    return '★'
            
            # Erste zwei Zeilen definieren
            matrix.append(['○', '□', '◇'])
            matrix.append(['□', '△', '★'])
            
            # Dritte Zeile ist Kombination
            third_row = []
            for i in range(3):
                combined = combine_shapes(matrix[0][i], matrix[1][i])
                third_row.append(combined)
            matrix.append(third_row)
            
            answer = third_row[2]
            matrix[2][2] = '?'
            explanation = "Dritte Zeile = Kombination der Formen aus Zeile 1 und 2"
            
        else:  # expert
            # 4x4 Matrix mit mehreren gleichzeitigen Regeln
            matrix_size = 4
            matrix = []
            
            # Komplexe Regeln für 4x4
            for i in range(matrix_size):
                row = []
                for j in range(matrix_size):
                    # Regel: Form basiert auf Position (i+j) und Rotation
                    shape_idx = (i + j) % len(shapes)
                    if (i + j) % 2 == 0:
                        row.append(shapes[shape_idx])
                    else:
                        # Verwende gefüllte Version wenn möglich
                        filled_map = {'○': '●', '□': '■', '△': '▲', '◇': '◆'}
                        shape = shapes[shape_idx]
                        row.append(filled_map.get(shape, shape))
                matrix.append(row)
            
            answer = matrix[3][3]
            matrix[3][3] = '?'
            explanation = "Position (i+j) bestimmt Form, gerade Summe = ungefüllt, ungerade = gefüllt"
        
        return {
            'type': 'matrix_geometric',
            'matrix': matrix,
            'answer': answer,
            'options': random.sample(shapes, 4) if answer not in shapes[:4] else None,
            'explanation': explanation,
            'question': 'Welche geometrische Form gehört in das Fragezeichen-Feld?'
        }
    
    @staticmethod
    def generate_wuerfel(difficulty: str) -> Dict:
        """Erweiterte Würfel-Aufgaben mit Mustern"""
        
        if difficulty == 'easy':
            # Standard-Würfel mit Zahlen
            standard_cube = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
            top = random.randint(1, 6)
            question = f"Ein Würfel zeigt oben die {top}. Welche Zahl ist unten?"
            answer = standard_cube[top]
            explanation = "Bei einem Standard-Würfel ergeben gegenüberliegende Seiten immer 7."
            
        elif difficulty == 'medium':
            # Würfel mit Symbolen
            faces = {
                'oben': '○',
                'unten': '●',
                'vorne': '□',
                'hinten': '■',
                'rechts': '△',
                'links': '▲'
            }
            
            # Kippen nach vorne
            question = "Würfel mit ○ oben, □ vorne. Nach Vorwärtskippen: Was ist oben?"
            answer = '■'  # hinten wird zu oben
            explanation = "Beim Vorwärtskippen: hinten→oben, oben→vorne, vorne→unten, unten→hinten"
            
        elif difficulty == 'hard':
            # Würfelnetz mit Mustern
            net_patterns = [
                {
                    'net': [
                        ['', '○', '', ''],
                        ['□', '●', '△', '■'],
                        ['', '▲', '', ''],
                        ['', '◇', '', '']
                    ],
                    'question': 'Welche Symbole liegen sich im gefalteten Würfel gegenüber?',
                    'pairs': [('○', '◇'), ('□', '■'), ('●', '▲')],
                    'answer': '○-◇, □-■, ●-▲'
                }
            ]
            
            pattern = random.choice(net_patterns)
            question = pattern['question']
            answer = pattern['answer']
            explanation = "Im Würfelnetz: Gegenüberliegende Flächen sind nie benachbart"
            
        else:  # expert
            # Komplexe 3D-Rotation mit mehreren Achsen
            question = "Würfel rotiert 90° um X-Achse, dann 180° um Y-Achse. Ausgangsposition: 1 oben, 2 vorne. Endposition?"
            answer = "4 oben, 5 vorne"
            explanation = "Mehrfache Rotationen: Verfolgen Sie jede Fläche durch alle Transformationen"
        
        return {
            'type': 'wuerfel',
            'question': question,
            'answer': answer,
            'explanation': explanation
        }
    
    @staticmethod
    def generate_figure_analogy(difficulty: str) -> Dict:
        """Generiert Analogien mit geometrischen Figuren"""
        
        analogies = {
            'easy': [
                {
                    'pair1': ('○', '●'),  # ungefüllt zu gefüllt
                    'pair2': ('□', '?'),
                    'options': ['■', '▲', '◇', '○'],
                    'answer': 0,
                    'explanation': 'Kreis:gefüllter Kreis = Quadrat:gefülltes Quadrat'
                },
                {
                    'pair1': ('△', '▽'),  # Spiegelung
                    'pair2': ('□', '?'),
                    'options': ['◇', '■', '○', '▭'],
                    'answer': 0,
                    'explanation': 'Dreieck nach oben:Dreieck nach unten = Quadrat:Raute (45° Rotation)'
                }
            ],
            'medium': [
                {
                    'pair1': ('○→●', '●→◐'),  # Progressive Füllung
                    'pair2': ('□→■', '■→?'),
                    'options': ['▦', '□', '▣', '▤'],
                    'answer': 2,
                    'explanation': 'Progression: leer → voll → Muster'
                }
            ],
            'hard': [
                {
                    'pair1': ('○+□', '◈'),  # Kombination
                    'pair2': ('△+○', '?'),
                    'options': ['⊙', '◉', '⬟', '▲'],
                    'answer': 2,
                    'explanation': 'Geometrische Überlagerung: Kreis+Quadrat=Quadrat mit Kreis, Dreieck+Kreis=Sechseck'
                }
            ]
        }
        
        analogy_data = random.choice(analogies.get(difficulty, analogies['easy']))
        
        return {
            'type': 'figure_analogy',
            'pair1': analogy_data['pair1'],
            'pair2': analogy_data['pair2'],
            'options': analogy_data['options'],
            'answer': analogy_data['answer'],
            'explanation': analogy_data['explanation'],
            'question': f"{analogy_data['pair1'][0]} : {analogy_data['pair1'][1]} = {analogy_data['pair2'][0]} : ?"
        }
    
    @staticmethod
    def generate_paper_folding(difficulty: str) -> Dict:
        """Generiert Papierfalt-Aufgaben (räumliches Denken)"""
        
        if difficulty == 'easy':
            # Einfache Faltung
            steps = [
                "1. Quadratisches Papier",
                "2. Einmal in der Mitte horizontal falten",
                "3. Loch in die Mitte stanzen"
            ]
            question = "Wie sieht das Papier entfaltet aus?"
            answer = "Zwei Löcher übereinander in der Mitte"
            options = [
                "Ein Loch in der Mitte",
                "Zwei Löcher übereinander in der Mitte",
                "Vier Löcher in den Ecken",
                "Zwei Löcher nebeneinander"
            ]
            correct = 1
            explanation = "Horizontale Faltung → Loch geht durch beide Lagen → 2 Löcher übereinander"
            
        elif difficulty == 'medium':
            # Zweifache Faltung
            steps = [
                "1. Quadratisches Papier",
                "2. Horizontal in der Mitte falten",
                "3. Vertikal in der Mitte falten",
                "4. Loch in eine Ecke stanzen"
            ]
            question = "Wie viele Löcher nach dem Entfalten?"
            answer = 4
            options = [1, 2, 3, 4]
            correct = 3
            explanation = "Zweifache Faltung = 4 Lagen → 4 Löcher (eines in jeder Ecke)"
            
        else:  # hard/expert
            # Komplexe Faltung
            steps = [
                "1. Quadrat diagonal falten (Dreieck)",
                "2. Nochmals in der Mitte falten",
                "3. Loch nahe der Spitze stanzen"
            ]
            question = "Muster nach dem Entfalten?"
            answer = "4 Löcher in symmetrischem Muster um den Mittelpunkt"
            options = [
                "Zufällig verteilte Löcher",
                "Löcher in einer Linie",
                "4 Löcher in symmetrischem Muster um den Mittelpunkt",
                "8 Löcher in zwei Kreisen"
            ]
            correct = 2
            explanation = "Diagonale Faltungen erzeugen rotationssymmetrische Muster"
        
        return {
            'type': 'paper_folding',
            'steps': steps,
            'question': question,
            'options': options,
            'answer': correct,
            'explanation': explanation
        }
    
    @staticmethod
    def generate_tangram(difficulty: str) -> Dict:
        """Generiert Tangram-ähnliche Aufgaben"""
        
        if difficulty == 'easy':
            # Einfache Figurenerkennung
            pieces = ['großes △', 'großes △', 'mittleres △', 'kleines △', 'kleines △', '□', '◇']
            question = "Welche Figur KANN NICHT aus diesen Tangram-Teilen gelegt werden?"
            options = [
                "Quadrat",
                "Rechteck",
                "Kreis",
                "Parallelogramm"
            ]
            answer = 2  # Kreis
            explanation = "Ein Kreis kann nicht aus geraden Tangram-Teilen gebildet werden"
            
        elif difficulty == 'medium':
            # Anzahl Teile bestimmen
            question = "Ein Haus-Umriss soll mit Tangram gelegt werden. Mindestens wie viele Teile werden benötigt?"
            # Vereinfachte Darstellung
            house = """
               △
              ╱ ╲
             ╱   ╲
            ╱     ╲
           ╱───────╲
           │       │
           │   □   │
           │       │
           └───────┘
            """
            answer = 5
            options = [3, 4, 5, 6]
            correct = 2
            explanation = "Dach: 1 großes Dreieck, Wände: 2 Dreiecke, Basis: 1 Quadrat + 1 Parallelogramm = 5 Teile"
            
        else:  # hard/expert
            # Komplexe Figur-Rekonstruktion
            question = "Welche Kombination von Teilen ergibt ein regelmäßiges Sechseck?"
            options = [
                "6 gleichseitige Dreiecke",
                "3 Rauten",
                "2 Trapeze + 2 Dreiecke",
                "Nicht möglich mit Standard-Tangram"
            ]
            answer = 0
            explanation = "6 gleichseitige Dreiecke können zu einem Sechseck arrangiert werden"
        
        return {
            'type': 'tangram',
            'question': question,
            'options': options,
            'answer': answer,
            'explanation': explanation
        }
    
    @staticmethod
    def generate_syllogismus(difficulty: str) -> Dict:
        """Erweiterte logische Schlussfolgerungen"""
        
        syllogisms = {
            'easy': [
                {
                    'premises': [
                        'Alle Richter sind Juristen.',
                        'Einige Juristen sind Anwälte.',
                        'Herr Meyer ist Richter.'
                    ],
                    'conclusions': [
                        'Herr Meyer ist Jurist.',
                        'Herr Meyer ist Anwalt.',
                        'Alle Anwälte sind Richter.',
                        'Einige Richter sind Anwälte.'
                    ],
                    'valid': [0],
                    'explanation': 'Aus "Alle Richter sind Juristen" und "Herr Meyer ist Richter" folgt zwingend "Herr Meyer ist Jurist".'
                }
            ],
            'medium': [
                {
                    'premises': [
                        'Kein Verbrechen bleibt ungestraft.',
                        'Einige Taten bleiben ungestraft.',
                        'Alle Verbrechen sind Taten.'
                    ],
                    'conclusions': [
                        'Einige Taten sind keine Verbrechen.',
                        'Alle Taten sind Verbrechen.',
                        'Keine Taten bleiben ungestraft.',
                        'Alle ungestraften Taten sind keine Verbrechen.'
                    ],
                    'valid': [0, 3],
                    'explanation': 'Wenn einige Taten ungestraft bleiben und kein Verbrechen ungestraft bleibt, müssen diese Taten keine Verbrechen sein.'
                }
            ],
            'hard': [
                {
                    'premises': [
                        'Wenn die Revision zulässig ist, wird sie auch begründet geprüft.',
                        'Die Revision wurde nicht begründet geprüft.',
                        'Entweder ist die Revision unzulässig oder sie wurde zurückgenommen.'
                    ],
                    'conclusions': [
                        'Die Revision ist unzulässig.',
                        'Die Revision wurde zurückgenommen.',
                        'Die Revision ist unzulässig oder wurde zurückgenommen.',
                        'Die Revision ist zulässig und wurde zurückgenommen.'
                    ],
                    'valid': [2],
                    'explanation': 'Modus tollens: Wenn A→B und nicht-B, dann nicht-A. Also ist die Revision nicht zulässig.'
                }
            ]
        }
        
        syllo = random.choice(syllogisms.get(difficulty, syllogisms['easy']))
        
        return {
            'type': 'syllogismus',
            'premises': syllo['premises'],
            'conclusions': syllo['conclusions'],
            'question': 'Welche Schlussfolgerung(en) sind logisch gültig?',
            'valid_indices': syllo['valid'],
            'explanation': syllo['explanation']
        }

# Haupttest-Engine
class TestEngine:
    """Erweiterte Test-Engine mit allen Kategorien"""
    
    def __init__(self):
        self.generators = {
            'Rechtschreibung': DeutschTest.generate_rechtschreibung,
            'Kommasetzung': DeutschTest.generate_kommasetzung,
            'Diktat': DeutschTest.generate_diktat,
            'Dreisatz': MathematikTest.generate_dreisatz,
            'Prozentrechnung': MathematikTest.generate_prozentrechnung,
            'Zeitrechnung': MathematikTest.generate_zeitrechnung,
            'Textverständnis': TextverstaendnisTest.generate_text_comprehension,
            'Politik': AllgemeinwissenTest.generate_politik,
            'Rechtskunde': AllgemeinwissenTest.generate_recht,
            'Hessen-Wissen': AllgemeinwissenTest.generate_hessen,
            'Merkfähigkeit': KonzentrationsTest.generate_merkfaehigkeit,
            'Konzentration': KonzentrationsTest.generate_konzentration,
            'Zahlenreihen': LogikTest.generate_zahlenreihe,
            'Würfel': LogikTest.generate_wuerfel,
            'Syllogismen': LogikTest.generate_syllogismus,
        }
        
        self.categories = {
            'Deutsch': ['Rechtschreibung', 'Kommasetzung', 'Diktat'],
            'Mathematik': ['Dreisatz', 'Prozentrechnung', 'Zeitrechnung'],
            'Textverständnis': ['Textverständnis'],
            'Allgemeinwissen': ['Politik', 'Rechtskunde', 'Hessen-Wissen'],
            'Konzentration': ['Merkfähigkeit', 'Konzentration'],
            'Logik & IQ': ['Zahlenreihen', 'Würfel', 'Syllogismen'],
            'Kompletttest': list(self.generators.keys())
        }
    
    def create_test(self, category: str, difficulty: str, num_questions: int = 10) -> List[Dict]:
        """Erstellt einen Test basierend auf Kategorie"""
        
        questions = []
        
        if category == 'Kompletttest':
            # Mische alle Kategorien
            for _ in range(num_questions):
                gen_name = random.choice(list(self.generators.keys()))
                generator = self.generators[gen_name]
                question = generator(difficulty)
                question['category'] = gen_name
                questions.append(question)
        else:
            # Spezifische Kategorie
            subcategories = self.categories.get(category, [category])
            for _ in range(num_questions):
                subcat = random.choice(subcategories)
                if subcat in self.generators:
                    generator = self.generators[subcat]
                    question = generator(difficulty)
                    question['category'] = subcat
                    questions.append(question)
        
        return questions
    
    def evaluate_answer(self, question: Dict, user_answer: Any) -> Tuple[bool, str]:
        """Bewertet eine Antwort basierend auf Fragetyp"""
        
        correct = False
        
        # Numerische Antworten
        if question['type'] in ['zahlenreihe', 'dreisatz', 'prozent', 'konzentration_zaehlen']:
            try:
                correct = abs(float(user_answer) - float(question['answer'])) < 0.01
            except (ValueError, TypeError):
                correct = False
                
        # Multiple Choice
        elif question['type'] in ['rechtschreibung', 'politik', 'recht', 'hessen', 'textverstaendnis']:
            correct = user_answer == question['answer']
            
        # Text-Antworten
        elif question['type'] in ['zeitrechnung', 'merkfaehigkeit_zahlen']:
            correct = str(user_answer).strip() == str(question['answer']).strip()
            
        # Spezielle Typen
        elif question['type'] == 'diktat':
            # Vereinfachte Bewertung für Demo
            correct = user_answer is not None
            
        elif question['type'] == 'syllogismus':
            # Prüfe ob alle validen Indizes ausgewählt wurden
            if isinstance(user_answer, list):
                correct = set(user_answer) == set(question['valid_indices'])
            else:
                correct = False
        
        return correct, question.get('explanation', 'Keine Erklärung verfügbar')
    
    def calculate_detailed_score(self, results: List[Dict], difficulty: str) -> Dict:
        """Berechnet detaillierte Bewertung mit Analyse"""
        
        total = len(results)
        correct = sum(1 for r in results if r['correct'])
        
        # Basis-Score
        percentage = (correct / total * 100) if total > 0 else 0
        
        # Schwierigkeits-Multiplikator
        difficulty_multiplier = {
            'easy': 1.0,
            'medium': 1.5,
            'hard': 2.0,
            'expert': 3.0
        }
        
        # Zeit-Analyse
        avg_time = np.mean([r['time'] for r in results]) if results else 0
        time_bonus = max(0, (60 - avg_time) * 0.5) if avg_time > 0 else 0
        
        # Kategorie-Analyse
        category_performance = {}
        for result in results:
            cat = result.get('category', 'Unbekannt')
            if cat not in category_performance:
                category_performance[cat] = {'correct': 0, 'total': 0}
            category_performance[cat]['total'] += 1
            if result['correct']:
                category_performance[cat]['correct'] += 1
        
        # Schwache und starke Bereiche identifizieren
        weak_areas = []
        strong_areas = []
        
        for cat, perf in category_performance.items():
            success_rate = (perf['correct'] / perf['total'] * 100) if perf['total'] > 0 else 0
            if success_rate < 50:
                weak_areas.append(cat)
            elif success_rate >= 80:
                strong_areas.append(cat)
        
        # Finaler Score
        final_score = percentage * difficulty_multiplier[difficulty] + time_bonus
        
        # Note/Bewertung
        if final_score >= 90:
            grade = '1 - Hervorragend'
            emoji = '🌟'
        elif final_score >= 80:
            grade = '2 - Gut'
            emoji = '👍'
        elif final_score >= 70:
            grade = '3 - Befriedigend'
            emoji = '✓'
        elif final_score >= 60:
            grade = '4 - Ausreichend'
            emoji = '📈'
        else:
            grade = '5 - Mangelhaft'
            emoji = '💪'
        
        return {
            'percentage': percentage,
            'final_score': final_score,
            'grade': grade,
            'emoji': emoji,
            'time_bonus': time_bonus,
            'avg_time': avg_time,
            'category_performance': category_performance,
            'weak_areas': weak_areas,
            'strong_areas': strong_areas,
            'total_questions': total,
            'correct_answers': correct
        }

# Lernanalyse und Empfehlungen
class LernAnalyse:
    """KI-basierte Lernanalyse und Empfehlungen"""
    
    @staticmethod
    def analyze_performance(user_stats: Dict) -> Dict:
        """Analysiert die Gesamtperformance und gibt Empfehlungen"""
        
        recommendations = []
        
        # Analysiere schwache Bereiche
        if 'category_performance' in user_stats:
            for category, performance in user_stats['category_performance'].items():
                if performance['total'] > 0:
                    success_rate = performance['correct'] / performance['total']
                    
                    if success_rate < 0.5:
                        recommendations.append({
                            'category': category,
                            'priority': 'Hoch',
                            'message': f'Fokussieren Sie sich auf {category}. Erfolgsquote nur {success_rate*100:.0f}%',
                            'exercises': f'Mindestens 20 Übungen in {category} empfohlen'
                        })
                    elif success_rate < 0.7:
                        recommendations.append({
                            'category': category,
                            'priority': 'Mittel',
                            'message': f'{category} verbessern. Erfolgsquote: {success_rate*100:.0f}%',
                            'exercises': f'10 weitere Übungen in {category} empfohlen'
                        })
        
        # Zeitmanagement
        if 'avg_time' in user_stats and user_stats['avg_time'] > 60:
            recommendations.append({
                'category': 'Zeitmanagement',
                'priority': 'Hoch',
                'message': f'Durchschnittliche Zeit pro Aufgabe: {user_stats["avg_time"]:.0f}s. Ziel: unter 60s',
                'exercises': 'Üben Sie mit aktiviertem Zeitlimit'
            })
        
        # Lernplan erstellen
        study_plan = LernAnalyse.create_study_plan(user_stats, recommendations)
        
        return {
            'recommendations': recommendations,
            'study_plan': study_plan,
            'estimated_ready_date': LernAnalyse.estimate_readiness(user_stats)
        }
    
    @staticmethod
    def create_study_plan(stats: Dict, recommendations: List) -> List[Dict]:
        """Erstellt einen personalisierten Lernplan"""
        
        plan = []
        days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
        
        # Priorisiere schwache Bereiche
        high_priority = [r for r in recommendations if r['priority'] == 'Hoch']
        medium_priority = [r for r in recommendations if r['priority'] == 'Mittel']
        
        for i, day in enumerate(days):
            daily_plan = {
                'day': day,
                'duration': '45 Minuten',
                'focus_areas': [],
                'exercises': []
            }
            
            # Verteile Schwerpunkte
            if i < len(high_priority):
                daily_plan['focus_areas'].append(high_priority[i]['category'])
                daily_plan['exercises'].append(f"20 Aufgaben {high_priority[i]['category']}")
            elif i - len(high_priority) < len(medium_priority):
                idx = i - len(high_priority)
                daily_plan['focus_areas'].append(medium_priority[idx]['category'])
                daily_plan['exercises'].append(f"15 Aufgaben {medium_priority[idx]['category']}")
            else:
                # Gemischtes Training
                daily_plan['focus_areas'].append('Kompletttest')
                daily_plan['exercises'].append('1 Kompletttest (20 Fragen)')
            
            # Füge immer etwas Wiederholung hinzu
            daily_plan['exercises'].append('5 Wiederholungsaufgaben')
            
            plan.append(daily_plan)
        
        return plan
    
    @staticmethod
    def estimate_readiness(stats: Dict) -> str:
        """Schätzt, wann der Nutzer bereit für den Test ist"""
        
        if 'total_tests' not in stats:
            return "Noch keine Daten für Prognose"
        
        # Vereinfachte Berechnung
        tests_done = stats.get('total_tests', 0)
        avg_score = stats.get('avg_score', 0)
        
        if avg_score >= 80:
            return "Sie sind bereit für den Test! ✅"
        elif avg_score >= 70:
            days_needed = 7
        elif avg_score >= 60:
            days_needed = 14
        else:
            days_needed = 21
        
        target_date = datetime.now() + timedelta(days=days_needed)
        return f"Voraussichtlich bereit am: {target_date.strftime('%d.%m.%Y')}"

# Hauptfunktion
def main():
    """Hauptfunktion der Streamlit-App"""
    
    # Header mit Logo und Titel
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <h1 style='text-align: center; color: #2c3e50;'>
            ⚖️ Justiz Einstellungstest<br>
            <span style='font-size: 0.6em; color: #7f8c8d;'>Professionelles Trainingssystem</span>
        </h1>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Testeinstellungen")
        
        # Benutzer
        username = st.text_input("👤 Benutzername", value="Anonym", key="username")
        
        st.divider()
        
        # Testmodus
        test_mode = st.selectbox(
            "📚 Testmodus",
            ['Training', 'Prüfungssimulation', 'Lernanalyse']
        )
        
        if test_mode in ['Training', 'Prüfungssimulation']:
            # Kategorie-Auswahl
            category = st.selectbox(
                "📂 Kategorie",
                ['Deutsch', 'Mathematik', 'Textverständnis', 'Allgemeinwissen', 
                 'Konzentration', 'Logik & IQ', 'Kompletttest']
            )
            
            # Schwierigkeit
            difficulty = st.select_slider(
                "🎯 Schwierigkeit",
                options=['easy', 'medium', 'hard', 'expert'],
                value='medium',
                format_func=lambda x: {
                    'easy': '🟢 Leicht',
                    'medium': '🟡 Mittel',
                    'hard': '🟠 Schwer',
                    'expert': '🔴 Experte'
                }[x]
            )
            
            # Anzahl Fragen
            if test_mode == 'Training':
                num_questions = st.slider("❓ Anzahl Fragen", 5, 30, 10)
            else:
                # Prüfungssimulation hat feste Anzahl
                num_questions = 30
                st.info("Prüfungssimulation: 30 Fragen in 60 Minuten")
            
            # Zeitlimit
            time_limit = st.checkbox("⏱️ Zeitlimit", value=True)
            if time_limit:
                if test_mode == 'Training':
                    time_per_question = st.slider("Sekunden pro Frage", 30, 120, 60)
                else:
                    time_per_question = 120  # 2 Minuten pro Frage in Prüfung
            else:
                time_per_