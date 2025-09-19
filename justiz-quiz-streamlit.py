"""
Justizfachwirt/in Einstellungstest - Interaktives Trainingstool
Professionelle Version mit Streamlit
Installation: pip install streamlit pandas numpy matplotlib plotly
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
from typing import Dict, List, Tuple, Any
import plotly.express as px
import plotly.graph_objects as go

# Seitenkonfiguration
st.set_page_config(
    page_title="Justiz IQ-Training",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für besseres Design
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #667eea;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #5a67d8;
        transform: translateY(-2px);
    }
    .correct-answer {
        background-color: #d4edda;
        border: 2px solid #28a745;
        padding: 10px;
        border-radius: 5px;
    }
    .incorrect-answer {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        padding: 10px;
        border-radius: 5px;
    }
    .explanation-box {
        background-color: #e8f4fd;
        border-left: 4px solid #0066cc;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisierung des Session State
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_test = None
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.test_history = []
    st.session_state.all_time_stats = {
        'total_tests': 0,
        'total_questions': 0,
        'correct_answers': 0,
        'avg_time': 0,
        'best_score': 0,
        'category_stats': {}
    }
    st.session_state.current_answer = None
    st.session_state.question_start_time = None
    st.session_state.test_active = False
    st.session_state.show_explanation = False
    st.session_state.user_profile = {
        'name': 'Anonym',
        'created': datetime.now().isoformat(),
        'last_login': datetime.now().isoformat()
    }

class QuestionGenerator:
    """Zentrale Klasse für die Generierung aller Fragetypen"""
    
    @staticmethod
    def generate_number_sequence(difficulty: str) -> Dict:
        """Generiert Zahlenreihen mit verschiedenen Mustern"""
        
        patterns = {
            'easy': [
                ('arithmetic', lambda n, d: n + d, 'Addition von {}'),
                ('geometric', lambda n, r: n * r, 'Multiplikation mit {}'),
                ('square', lambda i, _: i**2, 'Quadratzahlen'),
            ],
            'medium': [
                ('fibonacci', None, 'Fibonacci-Folge'),
                ('prime', None, 'Primzahlen'),
                ('triangular', lambda i, _: i*(i+1)//2, 'Dreieckszahlen'),
            ],
            'hard': [
                ('alternating', None, 'Alternierende Operation'),
                ('quadratic', lambda i, _: i**2 + i + 1, 'Quadratisch: n² + n + 1'),
                ('factorial', None, 'Fakultäten'),
            ],
            'expert': [
                ('recursive', None, 'Rekursive Formel'),
                ('composite', None, 'Zusammengesetzte Operation'),
                ('modular', None, 'Modulare Arithmetik'),
            ]
        }
        
        pattern_list = patterns.get(difficulty, patterns['easy'])
        pattern_type, func, explanation = random.choice(pattern_list)
        
        if pattern_type == 'arithmetic':
            d = random.randint(2, 10)
            start = random.randint(1, 20)
            sequence = [start + i*d for i in range(5)]
            explanation = explanation.format(d)
            
        elif pattern_type == 'geometric':
            r = random.randint(2, 4)
            start = random.randint(1, 5)
            sequence = [start * (r**i) for i in range(5)]
            explanation = explanation.format(r)
            
        elif pattern_type == 'square':
            start = random.randint(1, 5)
            sequence = [(start+i)**2 for i in range(5)]
            
        elif pattern_type == 'fibonacci':
            a, b = random.randint(1, 3), random.randint(1, 3)
            sequence = [a, b]
            for _ in range(3):
                sequence.append(sequence[-1] + sequence[-2])
                
        elif pattern_type == 'prime':
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
            start = random.randint(0, 10)
            sequence = primes[start:start+5]
            
        elif pattern_type == 'alternating':
            ops = [('+', random.randint(2, 5)), ('*', random.randint(2, 3))]
            start = random.randint(2, 5)
            sequence = [start]
            for i in range(4):
                op, val = ops[i % 2]
                if op == '+':
                    sequence.append(sequence[-1] + val)
                else:
                    sequence.append(sequence[-1] * val)
            explanation = f"Abwechselnd +{ops[0][1]} und ×{ops[1][1]}"
            
        else:
            # Fallback auf einfache arithmetische Folge
            d = random.randint(3, 8)
            start = random.randint(5, 15)
            sequence = [start + i*d for i in range(5)]
            explanation = f"Addition von {d}"
        
        return {
            'type': 'number_sequence',
            'sequence': sequence[:-1],
            'answer': sequence[-1],
            'explanation': explanation,
            'question': 'Setzen Sie die Zahlenreihe fort:'
        }
    
    @staticmethod
    def generate_matrix(difficulty: str) -> Dict:
        """Generiert Matrizenaufgaben"""
        
        size = 3 if difficulty in ['easy', 'medium'] else 4
        matrix = []
        
        if difficulty == 'easy':
            # Einfache Zeilensumme
            target_sum = random.randint(15, 30)
            for i in range(size):
                row = []
                remaining = target_sum
                for j in range(size - 1):
                    val = random.randint(1, remaining - (size - j - 1))
                    row.append(val)
                    remaining -= val
                row.append(remaining)
                matrix.append(row)
            answer = matrix[-1][-1]
            matrix[-1][-1] = '?'
            explanation = f"Jede Zeile summiert sich zu {target_sum}"
            
        elif difficulty == 'medium':
            # Multiplikationsmuster
            for i in range(size):
                base = random.randint(2, 6)
                row = [base * (j+1) for j in range(size)]
                matrix.append(row)
            answer = matrix[-1][-1]
            matrix[-1][-1] = '?'
            explanation = "Jede Zeile folgt einem Multiplikationsmuster"
            
        else:
            # Komplexe Muster
            for i in range(size):
                row = []
                for j in range(size):
                    val = (i+1) * (j+1) + random.randint(0, 2)
                    row.append(val)
                matrix.append(row)
            answer = matrix[-1][-1]
            matrix[-1][-1] = '?'
            explanation = "Zeilen- und Spaltenindex beeinflussen den Wert"
        
        return {
            'type': 'matrix',
            'matrix': matrix,
            'answer': answer,
            'explanation': explanation,
            'question': 'Welche Zahl gehört in das Fragezeichen-Feld?'
        }
    
    @staticmethod
    def generate_logic_puzzle(difficulty: str) -> Dict:
        """Generiert logische Schlussfolgerungen"""
        
        puzzles = {
            'easy': [
                {
                    'premises': [
                        'Alle Beamten haben eine Ausbildung.',
                        'Herr Schmidt ist Beamter.',
                    ],
                    'options': [
                        'Herr Schmidt hat eine Ausbildung.',
                        'Herr Schmidt hat keine Ausbildung.',
                        'Alle mit Ausbildung sind Beamte.',
                        'Keine Aussage möglich.'
                    ],
                    'answer': 0,
                    'explanation': 'Logischer Schluss: Wenn alle Beamten eine Ausbildung haben und Herr Schmidt Beamter ist, hat er eine Ausbildung.'
                }
            ],
            'medium': [
                {
                    'premises': [
                        'Einige Verfahren sind öffentlich.',
                        'Alle Strafverfahren sind Verfahren.',
                        'Kein Jugendstrafverfahren ist öffentlich.'
                    ],
                    'options': [
                        'Einige Strafverfahren sind nicht öffentlich.',
                        'Alle Jugendstrafverfahren sind Strafverfahren.',
                        'Kein Strafverfahren ist öffentlich.',
                        'Beides A und B können wahr sein.'
                    ],
                    'answer': 3,
                    'explanation': 'Aus den Prämissen folgt, dass einige Strafverfahren nicht öffentlich sind (die Jugendstrafverfahren).'
                }
            ],
            'hard': [
                {
                    'premises': [
                        'Wenn eine Frist versäumt wird, ist der Antrag unzulässig.',
                        'Der Antrag ist zulässig oder wird abgewiesen.',
                        'Der Antrag wurde nicht abgewiesen.'
                    ],
                    'options': [
                        'Die Frist wurde nicht versäumt.',
                        'Die Frist wurde versäumt.',
                        'Der Antrag ist unzulässig.',
                        'Keine eindeutige Aussage möglich.'
                    ],
                    'answer': 0,
                    'explanation': 'Wenn der Antrag zulässig ist (da nicht abgewiesen), kann die Frist nicht versäumt worden sein.'
                }
            ]
        }
        
        puzzle_list = puzzles.get(difficulty, puzzles['easy'])
        puzzle = random.choice(puzzle_list)
        
        return {
            'type': 'logic',
            'premises': puzzle['premises'],
            'options': puzzle['options'],
            'answer': puzzle['answer'],
            'explanation': puzzle['explanation'],
            'question': 'Welche Schlussfolgerung ist korrekt?'
        }
    
    @staticmethod
    def generate_analogy(difficulty: str) -> Dict:
        """Generiert Analogieaufgaben"""
        
        analogies = {
            'easy': [
                (['Richter', 'Urteil'], ['Staatsanwalt', '?'], 
                 ['Anklage', 'Verteidigung', 'Zeuge', 'Beweis'], 0,
                 'Der Richter fällt das Urteil, der Staatsanwalt erhebt die Anklage.'),
                
                (['Buch', 'Seite'], ['Gesetz', '?'],
                 ['Paragraph', 'Artikel', 'Absatz', 'Kapitel'], 0,
                 'Ein Buch besteht aus Seiten, ein Gesetz aus Paragraphen.'),
            ],
            'medium': [
                (['Revision', 'BGH'], ['Berufung', '?'],
                 ['OLG', 'LG', 'AG', 'BVerfG'], 0,
                 'Revision geht zum BGH, Berufung zum OLG.'),
            ],
            'hard': [
                (['Verjährung', 'Zeit'], ['Verwirkung', '?'],
                 ['Verhalten', 'Frist', 'Gesetz', 'Recht'], 0,
                 'Verjährung tritt durch Zeitablauf ein, Verwirkung durch Verhalten.'),
            ]
        }
        
        analogy_list = analogies.get(difficulty, analogies['easy'])
        analogy = random.choice(analogy_list)
        
        return {
            'type': 'analogy',
            'pair1': analogy[0],
            'pair2': analogy[1],
            'options': analogy[2],
            'answer': analogy[3],
            'explanation': analogy[4],
            'question': f'{analogy[0][0]} : {analogy[0][1]} = {analogy[1][0]} : ?'
        }
    
    @staticmethod
    def generate_spatial(difficulty: str) -> Dict:
        """Generiert räumliche Vorstellungsaufgaben"""
        
        shapes = ['□', '○', '△', '◇', '★', '▪', '▲', '◆']
        
        if difficulty == 'easy':
            # Einfache Rotation
            sequence = random.sample(shapes, 4)
            rotations = [0, 1, 2, 3]
            answer_idx = 3
            explanation = "Die Figur rotiert im Uhrzeigersinn"
        else:
            # Komplexere Muster
            base = random.sample(shapes, 3)
            sequence = []
            for i in range(4):
                sequence.append(base[i % 3])
            answer_idx = 3
            explanation = "Wiederholendes Muster alle 3 Schritte"
        
        return {
            'type': 'spatial',
            'sequence': sequence[:3],
            'options': random.sample(shapes, 4),
            'answer': answer_idx,
            'explanation': explanation,
            'question': 'Welche Figur folgt als nächstes?'
        }

class TestEngine:
    """Hauptklasse für die Testverwaltung"""
    
    def __init__(self):
        self.generator = QuestionGenerator()
        self.question_types = {
            'Zahlenreihen': self.generator.generate_number_sequence,
            'Matrizen': self.generator.generate_matrix,
            'Logik': self.generator.generate_logic_puzzle,
            'Analogien': self.generator.generate_analogy,
            'Räumlich': self.generator.generate_spatial
        }
    
    def create_test(self, category: str, difficulty: str, num_questions: int = 10) -> List[Dict]:
        """Erstellt einen kompletten Test"""
        questions = []
        
        if category == 'Gemischt':
            # Mische verschiedene Fragetypen
            for _ in range(num_questions):
                q_type = random.choice(list(self.question_types.keys()))
                question = self.question_types[q_type](difficulty)
                question['category'] = q_type
                questions.append(question)
        else:
            # Nur eine Kategorie
            for _ in range(num_questions):
                question = self.question_types[category](difficulty)
                question['category'] = category
                questions.append(question)
        
        return questions
    
    def evaluate_answer(self, question: Dict, user_answer: Any) -> Tuple[bool, str]:
        """Bewertet eine Antwort"""
        correct = False
        
        if question['type'] in ['number_sequence', 'matrix']:
            try:
                correct = int(user_answer) == int(question['answer'])
            except (ValueError, TypeError):
                correct = False
        elif question['type'] in ['logic', 'analogy', 'spatial']:
            correct = user_answer == question['answer']
        
        return correct, question['explanation']
    
    def calculate_score(self, correct: int, total: int, difficulty: str, avg_time: float) -> Dict:
        """Berechnet detaillierte Bewertung"""
        
        difficulty_multiplier = {
            'easy': 1.0,
            'medium': 1.5,
            'hard': 2.0,
            'expert': 3.0
        }
        
        base_score = (correct / total) * 100
        time_bonus = max(0, 60 - avg_time) * 0.5  # Bonus für schnelle Antworten
        difficulty_bonus = base_score * (difficulty_multiplier[difficulty] - 1)
        
        final_score = base_score + time_bonus + difficulty_bonus
        
        # Bewertung
        if final_score >= 90:
            grade = 'Hervorragend! 🌟'
            color = 'green'
        elif final_score >= 75:
            grade = 'Sehr gut! 👏'
            color = 'blue'
        elif final_score >= 60:
            grade = 'Gut! 👍'
            color = 'orange'
        else:
            grade = 'Weiter üben! 💪'
            color = 'red'
        
        return {
            'base_score': base_score,
            'time_bonus': time_bonus,
            'difficulty_bonus': difficulty_bonus,
            'final_score': final_score,
            'grade': grade,
            'color': color
        }

def main():
    """Hauptfunktion der Streamlit-App"""
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🧠 Justiz IQ-Training")
        st.markdown("### Professionelles Training für den Einstellungstest")
    
    # Sidebar für Einstellungen
    with st.sidebar:
        st.header("⚙️ Einstellungen")
        
        # Benutzerprofil
        st.subheader("👤 Benutzerprofil")
        name = st.text_input("Name", value=st.session_state.user_profile['name'])
        if name != st.session_state.user_profile['name']:
            st.session_state.user_profile['name'] = name
        
        st.divider()
        
        # Testeinstellungen
        st.subheader("📝 Testeinstellungen")
        category = st.selectbox(
            "Kategorie",
            ['Zahlenreihen', 'Matrizen', 'Logik', 'Analogien', 'Räumlich', 'Gemischt']
        )
        
        difficulty = st.select_slider(
            "Schwierigkeitsgrad",
            options=['easy', 'medium', 'hard', 'expert'],
            format_func=lambda x: {
                'easy': '🟢 Leicht',
                'medium': '🟡 Mittel', 
                'hard': '🟠 Schwer',
                'expert': '🔴 Experte'
            }[x]
        )
        
        num_questions = st.slider("Anzahl Fragen", 5, 20, 10)
        
        time_limit = st.checkbox("Zeitlimit aktivieren", value=True)
        if time_limit:
            seconds_per_question = st.slider("Sekunden pro Frage", 30, 120, 60)
        else:
            seconds_per_question = None
        
        st.divider()
        
        # Statistiken
        st.subheader("📊 Ihre Statistiken")
        stats = st.session_state.all_time_stats
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tests gesamt", stats['total_tests'])
            st.metric("Fragen gesamt", stats['total_questions'])
        with col2:
            if stats['total_questions'] > 0:
                accuracy = (stats['correct_answers'] / stats['total_questions'] * 100)
                st.metric("Genauigkeit", f"{accuracy:.1f}%")
            else:
                st.metric("Genauigkeit", "N/A")
            st.metric("Bester Score", f"{stats['best_score']:.1f}")
        
        # Reset Button
        if st.button("🔄 Statistiken zurücksetzen", type="secondary"):
            st.session_state.all_time_stats = {
                'total_tests': 0,
                'total_questions': 0,
                'correct_answers': 0,
                'avg_time': 0,
                'best_score': 0,
                'category_stats': {}
            }
            st.rerun()
    
    # Hauptbereich
    if not st.session_state.test_active:
        # Startbildschirm
        st.markdown("""
        ### Willkommen beim interaktiven Justiz-Trainingstool!
        
        Dieses professionelle Übungssystem bereitet Sie optimal auf den Einstellungstest vor:
        
        - 🎯 **Adaptive Schwierigkeit:** Passt sich Ihrem Niveau an
        - 📊 **Detaillierte Analysen:** Verfolgen Sie Ihren Fortschritt
        - 🧠 **KI-generierte Fragen:** Immer neue Herausforderungen
        - ⏱️ **Zeitdruck-Training:** Wie im echten Test
        - 📈 **Lernkurven:** Sehen Sie Ihre Verbesserung
        
        **Wählen Sie links Ihre Einstellungen und starten Sie den Test!**
        """)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 TEST STARTEN", type="primary", use_container_width=True):
                # Test initialisieren
                engine = TestEngine()
                st.session_state.current_test = engine.create_test(category, difficulty, num_questions)
                st.session_state.current_question = 0
                st.session_state.score = 0
                st.session_state.test_history = []
                st.session_state.test_active = True
                st.session_state.test_start_time = time.time()
                st.session_state.time_limit = seconds_per_question if time_limit else None
                st.rerun()
        
        # Zeige letzte Ergebnisse wenn vorhanden
        if len(st.session_state.test_history) > 0:
            st.divider()
            st.subheader("📈 Letzte Testergebnisse")
            
            # Erstelle DataFrame für Visualisierung
            df = pd.DataFrame(st.session_state.test_history)
            
            # Erfolgsquote Diagramm
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, len(df) + 1)),
                y=df['correct'].astype(int).cumsum() / (df.index + 1) * 100,
                mode='lines+markers',
                name='Erfolgsquote',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Erfolgsquote im Verlauf",
                xaxis_title="Frage",
                yaxis_title="Erfolgsquote (%)",
                yaxis=dict(range=[0, 100]),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Zeit pro Frage
            col1, col2 = st.columns(2)
            with col1:
                fig2 = px.bar(
                    df, 
                    x=df.index + 1, 
                    y='time',
                    title="Zeit pro Frage (Sekunden)",
                    color='correct',
                    color_discrete_map={True: 'green', False: 'red'}
                )
                fig2.update_xaxis(title="Frage")
                fig2.update_yaxis(title="Zeit (s)")
                st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                # Kategorie-Statistiken
                category_stats = df.groupby('category')['correct'].agg(['sum', 'count', 'mean'])
                category_stats['percentage'] = category_stats['mean'] * 100
                
                fig3 = px.bar(
                    category_stats.reset_index(),
                    x='category',
                    y='percentage',
                    title="Erfolg nach Kategorie",
                    color='percentage',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )
                fig3.update_yaxis(title="Erfolgsquote (%)")
                st.plotly_chart(fig3, use_container_width=True)
    
    else:
        # Test läuft
        test = st.session_state.current_test
        current_q = st.session_state.current_question
        
        if current_q < len(test):
            question = test[current_q]
            
            # Progress Bar
            progress = current_q / len(test)
            st.progress(progress, text=f"Frage {current_q + 1} von {len(test)}")
            
            # Timer wenn aktiviert
            if st.session_state.time_limit:
                if st.session_state.question_start_time is None:
                    st.session_state.question_start_time = time.time()
                
                time_elapsed = time.time() - st.session_state.question_start_time
                time_remaining = max(0, st.session_state.time_limit - time_elapsed)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    if time_remaining > 10:
                        st.info(f"⏱️ {int(time_remaining)}s")
                    else:
                        st.warning(f"⏱️ {int(time_remaining)}s")
                    
                    if time_remaining == 0 and not st.session_state.show_explanation:
                        st.session_state.show_explanation = True
                        st.rerun()
            
            # Frage anzeigen
            st.markdown(f"### {question['question']}")
            
            if question['type'] == 'number_sequence':
                st.markdown(f"### {' → '.join(map(str, question['sequence']))} → ?")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if not st.session_state.show_explanation:
                        answer = st.number_input(
                            "Ihre Antwort:",
                            key=f"answer_{current_q}",
                            step=1
                        )
                        st.session_state.current_answer = answer
            
            elif question['type'] == 'matrix':
                # Matrix anzeigen
                matrix_df = pd.DataFrame(question['matrix'])
                st.dataframe(
                    matrix_df,
                    hide_index=True,
                    use_container_width=False,
                    column_config={
                        str(i): st.column_config.TextColumn(
                            str(i),
                            width="small"
                        ) for i in range(len(question['matrix'][0]))
                    }
                )
                
                if not st.session_state.show_explanation:
                    answer = st.number_input(
                        "Welche Zahl gehört in das ?-Feld:",
                        key=f"answer_{current_q}",
                        step=1
                    )
                    st.session_state.current_answer = answer
            
            elif question['type'] in ['logic', 'analogy', 'spatial']:
                if question['type'] == 'logic':
                    st.markdown("**Prämissen:**")
                    for p in question['premises']:
                        st.markdown(f"- {p}")
                elif question['type'] == 'spatial':
                    st.markdown(f"### {' → '.join(question['sequence'])} → ?")
                
                if not st.session_state.show_explanation:
                    answer = st.radio(
                        "Wählen Sie die richtige Antwort:",
                        options=range(len(question['options'])),
                        format_func=lambda x: question['options'][x],
                        key=f"answer_{current_q}"
                    )
                    st.session_state.current_answer = answer
            
            # Antwort-Button oder Erklärung
            if not st.session_state.show_explanation:
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ Antwort prüfen", type="primary", use_container_width=True):
                        engine = TestEngine()
                        correct, explanation = engine.evaluate_answer(
                            question,
                            st.session_state.current_answer
                        )
                        
                        # Zeit speichern
                        if st.session_state.question_start_time:
                            time_taken = time.time() - st.session_state.question_start_time
                        else:
                            time_taken = 0
                        
                        # Ergebnis speichern
                        st.session_state.test_history.append({
                            'question': current_q + 1,
                            'correct': correct,
                            'time': round(time_taken, 2),
                            'category': question['category'],
                            'difficulty': difficulty
                        })
                        
                        if correct:
                            st.session_state.score += 1
                            st.session_state.all_time_stats['correct_answers'] += 1
                        
                        st.session_state.all_time_stats['total_questions'] += 1
                        st.session_state.show_explanation = True
                        st.rerun()
            else:
                # Zeige Ergebnis
                correct = st.session_state.test_history[-1]['correct']
                
                if correct:
                    st.success("✅ **Richtig!**")
                else:
                    st.error(f"❌ **Falsch!** Richtige Antwort: {question['answer']}")
                
                # Erklärung
                with st.expander("📚 Erklärung", expanded=True):
                    st.info(question['explanation'])
                
                # Nächste Frage Button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("Nächste Frage ➡️", type="primary", use_container_width=True):
                        st.session_state.current_question += 1
                        st.session_state.show_explanation = False
                        st.session_state.question_start_time = None
                        st.rerun()
        
        else:
            # Test beendet
            st.balloons()
            st.markdown("## 🎉 Test abgeschlossen!")
            
            # Berechne Ergebnisse
            engine = TestEngine()
            total = len(test)
            correct = st.session_state.score
            avg_time = np.mean([h['time'] for h in st.session_state.test_history])
            
            results = engine.calculate_score(correct, total, difficulty, avg_time)
            
            # Zeige Ergebnisse
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Richtige Antworten", f"{correct}/{total}")
            with col2:
                st.metric("Erfolgsquote", f"{results['base_score']:.1f}%")
            with col3:
                st.metric("Ø Zeit/Frage", f"{avg_time:.1f}s")
            with col4:
                st.metric("Gesamtpunktzahl", f"{results['final_score']:.1f}")
            
            # Bewertung
            st.markdown(f"### {results['grade']}")
            
            # Detaillierte Aufschlüsselung
            with st.expander("📊 Detaillierte Auswertung"):
                breakdown = pd.DataFrame({
                    'Komponente': ['Basis-Score', 'Zeit-Bonus', 'Schwierigkeits-Bonus', 'Gesamt'],
                    'Punkte': [
                        results['base_score'],
                        results['time_bonus'],
                        results['difficulty_bonus'],
                        results['final_score']
                    ]
                })
                
                fig = px.bar(
                    breakdown,
                    x='Komponente',
                    y='Punkte',
                    title="Punkteaufschlüsselung",
                    color='Komponente',
                    color_discrete_sequence=['blue', 'green', 'orange', 'red']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Statistiken updaten
            st.session_state.all_time_stats['total_tests'] += 1
            if results['final_score'] > st.session_state.all_time_stats['best_score']:
                st.session_state.all_time_stats['best_score'] = results['final_score']
            
            # Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Detaillierte Analyse", type="secondary", use_container_width=True):
                    st.session_state.test_active = False
                    st.rerun()
            with col2:
                if st.button("🔄 Neuer Test", type="primary", use_container_width=True):
                    st.session_state.test_active = False
                    st.session_state.current_question = 0
                    st.session_state.score = 0
                    st.rerun()

if __name__ == "__main__":
    main()
