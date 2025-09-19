"""
Justizfachwirt/in Einstellungstest - Komplettes Trainingssystem
Mit geometrischen Formen und räumlichem Denken
Installation: pip install streamlit pandas numpy matplotlib
Starten: streamlit run justiz_quiz.py
"""

import streamlit as st
import random
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Any

# Seitenkonfiguration
st.set_page_config(
    page_title="Justiz IQ-Training",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    .correct-answer {
        background: #d4edda;
        border: 2px solid #28a745;
        padding: 15px;
        border-radius: 10px;
    }
    .incorrect-answer {
        background: #f8d7da;
        border: 2px solid #dc3545;
        padding: 15px;
        border-radius: 10px;
    }
    .matrix-display {
        font-family: monospace;
        font-size: 24px;
        text-align: center;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State initialisieren
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_test = []
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.test_history = []
    st.session_state.test_active = False
    st.session_state.show_result = False
    st.session_state.current_answer = None

class GeometricPatternGenerator:
    """Generator für geometrische Muster und räumliche Aufgaben"""
    
    @staticmethod
    def generate_pattern_sequence(difficulty='medium'):
        """Generiert geometrische Musterfolgen"""
        
        shapes = ['○', '●', '□', '■', '△', '▲', '◇', '◆', '★', '☆']
        
        if difficulty == 'easy':
            # Einfache Wiederholung
            pattern = random.sample(shapes[:4], 3)
            sequence = pattern * 2
            answer = pattern[0]
            explanation = "Muster wiederholt sich alle 3 Formen"
            
        elif difficulty == 'medium':
            # Abwechselnd gefüllt/ungefüllt
            pairs = [('○', '●'), ('□', '■'), ('△', '▲')]
            pair = random.choice(pairs)
            sequence = [pair[0], pair[1]] * 3
            answer = pair[0]
            explanation = "Abwechselnd ungefüllt und gefüllt"
            
        elif difficulty == 'hard':
            # Rotation + Transformation
            base = ['○', '□', '△']
            sequence = []
            for i in range(6):
                idx = i % 3
                if i >= 3:
                    # Gefüllte Version in zweiter Hälfte
                    filled = {'○': '●', '□': '■', '△': '▲'}
                    sequence.append(filled.get(base[idx], base[idx]))
                else:
                    sequence.append(base[idx])
            answer = '●'  # Gefüllter Kreis
            explanation = "Erst ungefüllt (○□△), dann gefüllt (●■▲)"
            
        else:  # expert
            # Multiple Regeln
            sequence = []
            for i in range(6):
                if i % 2 == 0:
                    sequence.append(shapes[i // 2])
                else:
                    sequence.append(shapes[-(i // 2 + 1)])
            answer = shapes[3]
            explanation = "Komplexes Muster mit alternierenden Indizes"
        
        return {
            'type': 'pattern',
            'sequence': sequence[:6],
            'answer': answer,
            'explanation': explanation,
            'options': random.sample(shapes, 4) if answer not in random.sample(shapes, 4) else [answer] + random.sample([s for s in shapes if s != answer], 3)
        }
    
    @staticmethod
    def generate_matrix_pattern(difficulty='medium'):
        """Generiert 3x3 Matrix mit geometrischen Formen"""
        
        shapes = ['○', '□', '△', '◇', '★']
        
        if difficulty == 'easy':
            # Latin Square - jede Form einmal pro Zeile/Spalte
            size = 3
            used = shapes[:size]
            matrix = []
            for i in range(size):
                row = []
                for j in range(size):
                    idx = (i + j) % size
                    row.append(used[idx])
                matrix.append(row)
            
            # Verstecke letztes Element
            answer = matrix[2][2]
            matrix[2][2] = '?'
            explanation = "Jede Form erscheint in jeder Zeile und Spalte genau einmal"
            
        elif difficulty == 'medium':
            # Zeilen-Transformation
            matrix = [
                ['○', '□', '△'],
                ['●', '■', '▲'],
                ['○', '□', '?']
            ]
            answer = '△'
            explanation = "Zeilen alternieren zwischen ungefüllt und gefüllt"
            
        elif difficulty == 'hard':
            # Diagonale Regel
            matrix = [
                ['○', '□', '△'],
                ['□', '△', '○'],
                ['△', '?', '□']
            ]
            answer = '○'
            explanation = "Verschiebung um eine Position pro Zeile"
            
        else:  # expert
            # Komplexe Überlagerung
            matrix = [
                ['○', '□', '◇'],
                ['□', '△', '★'],
                ['◇', '★', '?']
            ]
            answer = '⬢'  # Hexagon als Kombination
            explanation = "Dritte Zeile kombiniert Eigenschaften der ersten beiden"
        
        return {
            'type': 'matrix',
            'matrix': matrix,
            'answer': answer,
            'explanation': explanation,
            'options': [answer] + random.sample([s for s in shapes if s != answer], 3)
        }
    
    @staticmethod
    def generate_spatial_rotation(difficulty='medium'):
        """Generiert räumliche Rotationsaufgaben"""
        
        if difficulty == 'easy':
            question = "Ein Würfel zeigt oben 3, vorne 2. Welche Zahl ist unten?"
            answer = 4
            explanation = "Gegenüberliegende Seiten eines Würfels ergeben immer 7. 3 oben → 4 unten"
            options = [2, 3, 4, 5]
            
        elif difficulty == 'medium':
            question = "L-förmiger Block wird 90° nach rechts gedreht. Welche Ansicht?"
            answer = "┐\n│\n└"
            explanation = "90° Rechtsdrehung verändert die Orientierung des L"
            options = ["┐\n│\n└", "└\n│\n┌", "┌\n│\n┘", "┘\n│\n┌"]
            
        elif difficulty == 'hard':
            question = "Würfel mit Symbolen: ○ oben, □ vorne, △ rechts. Nach Vorwärtskippen?"
            answer = "□ oben, ● unten"
            explanation = "Vorwärtskippen: vorne→oben, oben→hinten, unten→vorne"
            options = ["□ oben", "△ oben", "○ oben", "● oben"]
            
        else:  # expert
            question = "3D-Objekt: 2 Drehungen (90° um X, dann 180° um Y). Endposition?"
            answer = "Spiegelverkehrte Position"
            explanation = "Mehrfache Rotationen erfordern sequenzielles Denken"
            options = ["Original", "Gespiegelt", "Umgekehrt", "Spiegelverkehrt"]
        
        return {
            'type': 'spatial',
            'question': question,
            'answer': answer,
            'explanation': explanation,
            'options': options
        }
    
    @staticmethod
    def generate_paper_folding(difficulty='medium'):
        """Generiert Papierfalt-Aufgaben"""
        
        if difficulty == 'easy':
            question = "Papier einmal horizontal gefaltet, Loch in Mitte. Nach Entfalten?"
            answer = "2 Löcher übereinander"
            options = ["1 Loch", "2 Löcher übereinander", "2 Löcher nebeneinander", "4 Löcher"]
            explanation = "Eine Faltung = 2 Lagen = 2 Löcher"
            
        elif difficulty == 'medium':
            question = "Papier horizontal und vertikal gefaltet, Loch in Ecke. Wie viele Löcher?"
            answer = "4 Löcher"
            options = ["1 Loch", "2 Löcher", "3 Löcher", "4 Löcher"]
            explanation = "2 Faltungen = 4 Lagen = 4 Löcher"
            
        elif difficulty == 'hard':
            question = "Diagonal gefaltet, dann nochmals. Loch nahe Spitze. Muster?"
            answer = "4 symmetrische Löcher um Zentrum"
            options = ["Zufällig", "Linear", "4 symmetrische Löcher um Zentrum", "8 Löcher"]
            explanation = "Diagonale Faltungen erzeugen Rotationssymmetrie"
            
        else:  # expert
            question = "3 Faltungen: diagonal, horizontal, vertikal. 1 Loch. Endmuster?"
            answer = "8 Löcher in symmetrischem Muster"
            options = ["4 Löcher", "6 Löcher", "8 Löcher in symmetrischem Muster", "16 Löcher"]
            explanation = "3 Faltungen = 8 Lagen = 8 Löcher"
        
        return {
            'type': 'folding',
            'question': question,
            'answer': answer,
            'options': options,
            'explanation': explanation
        }

class NumberSequenceGenerator:
    """Generator für Zahlenreihen"""
    
    @staticmethod
    def generate_sequence(difficulty='medium'):
        """Generiert verschiedene Zahlenreihen"""
        
        if difficulty == 'easy':
            # Arithmetische Folge
            start = random.randint(2, 10)
            step = random.randint(2, 5)
            sequence = [start + i * step for i in range(6)]
            answer = sequence[5]
            explanation = f"Arithmetische Folge: +{step}"
            
        elif difficulty == 'medium':
            # Fibonacci-ähnlich
            a, b = random.randint(1, 3), random.randint(2, 4)
            sequence = [a, b]
            for _ in range(4):
                sequence.append(sequence[-1] + sequence[-2])
            answer = sequence[5]
            explanation = "Summe der zwei vorherigen Zahlen"
            
        elif difficulty == 'hard':
            # Alternierende Operationen
            start = random.randint(3, 7)
            sequence = [start]
            for i in range(5):
                if i % 2 == 0:
                    sequence.append(sequence[-1] * 2)
                else:
                    sequence.append(sequence[-1] + 3)
            answer = sequence[5]
            explanation = "Abwechselnd ×2 und +3"
            
        else:  # expert
            # Quadratzahlen + Konstante
            offset = random.randint(1, 5)
            sequence = [(i**2) + offset for i in range(1, 7)]
            answer = sequence[5]
            explanation = f"n² + {offset}"
        
        return {
            'type': 'number',
            'sequence': sequence[:5],
            'answer': answer,
            'explanation': explanation
        }

class LogicGenerator:
    """Generator für logische Aufgaben"""
    
    @staticmethod
    def generate_syllogism(difficulty='medium'):
        """Generiert logische Schlussfolgerungen"""
        
        syllogisms = {
            'easy': {
                'premises': [
                    "Alle Richter sind Juristen.",
                    "Herr Schmidt ist Richter."
                ],
                'conclusions': [
                    "Herr Schmidt ist Jurist.",
                    "Alle Juristen sind Richter.",
                    "Herr Schmidt ist kein Jurist.",
                    "Einige Richter sind keine Juristen."
                ],
                'correct': 0,
                'explanation': "Wenn alle Richter Juristen sind und Herr Schmidt Richter ist, muss er Jurist sein."
            },
            'medium': {
                'premises': [
                    "Kein Beamter darf Geschenke über 25€ annehmen.",
                    "Frau Müller ist Beamtin.",
                    "Das Geschenk hat einen Wert von 30€."
                ],
                'conclusions': [
                    "Frau Müller darf das Geschenk annehmen.",
                    "Frau Müller darf das Geschenk nicht annehmen.",
                    "Das Geschenk hat keinen Wert.",
                    "Frau Müller ist keine Beamtin."
                ],
                'correct': 1,
                'explanation': "Da das Geschenk über 25€ liegt und sie Beamtin ist, darf sie es nicht annehmen."
            },
            'hard': {
                'premises': [
                    "Wenn die Frist versäumt wird, ist der Antrag unzulässig.",
                    "Der Antrag ist zulässig.",
                    "Die Frist läuft morgen ab."
                ],
                'conclusions': [
                    "Die Frist wurde versäumt.",
                    "Die Frist wurde nicht versäumt.",
                    "Der Antrag ist unzulässig.",
                    "Die Frist ist irrelevant."
                ],
                'correct': 1,
                'explanation': "Da der Antrag zulässig ist, kann die Frist nicht versäumt worden sein."
            }
        }
        
        data = syllogisms.get(difficulty, syllogisms['medium'])
        return {
            'type': 'logic',
            'premises': data['premises'],
            'conclusions': data['conclusions'],
            'answer': data['correct'],
            'explanation': data['explanation']
        }

class TestEngine:
    """Hauptklasse für die Testverwaltung"""
    
    def __init__(self):
        self.generators = {
            'geometric': GeometricPatternGenerator(),
            'numbers': NumberSequenceGenerator(),
            'logic': LogicGenerator()
        }
    
    def create_test(self, test_type, difficulty, num_questions):
        """Erstellt einen Test mit verschiedenen Aufgabentypen"""
        
        questions = []
        
        if test_type == 'Geometrische Muster':
            for _ in range(num_questions):
                q_type = random.choice(['pattern', 'matrix'])
                if q_type == 'pattern':
                    questions.append(self.generators['geometric'].generate_pattern_sequence(difficulty))
                else:
                    questions.append(self.generators['geometric'].generate_matrix_pattern(difficulty))
                    
        elif test_type == 'Räumliches Denken':
            for _ in range(num_questions):
                q_type = random.choice(['spatial', 'folding'])
                if q_type == 'spatial':
                    questions.append(self.generators['geometric'].generate_spatial_rotation(difficulty))
                else:
                    questions.append(self.generators['geometric'].generate_paper_folding(difficulty))
                    
        elif test_type == 'Zahlenreihen':
            for _ in range(num_questions):
                questions.append(self.generators['numbers'].generate_sequence(difficulty))
                
        elif test_type == 'Logik':
            for _ in range(num_questions):
                questions.append(self.generators['logic'].generate_syllogism(difficulty))
                
        else:  # Gemischt
            for _ in range(num_questions):
                gen_type = random.choice(['geometric_pattern', 'geometric_matrix', 
                                         'spatial', 'folding', 'numbers', 'logic'])
                if gen_type == 'geometric_pattern':
                    questions.append(self.generators['geometric'].generate_pattern_sequence(difficulty))
                elif gen_type == 'geometric_matrix':
                    questions.append(self.generators['geometric'].generate_matrix_pattern(difficulty))
                elif gen_type == 'spatial':
                    questions.append(self.generators['geometric'].generate_spatial_rotation(difficulty))
                elif gen_type == 'folding':
                    questions.append(self.generators['geometric'].generate_paper_folding(difficulty))
                elif gen_type == 'numbers':
                    questions.append(self.generators['numbers'].generate_sequence(difficulty))
                else:
                    questions.append(self.generators['logic'].generate_syllogism(difficulty))
        
        return questions

def display_question(question, index):
    """Zeigt eine Frage an"""
    
    st.markdown(f"### Frage {index + 1}")
    
    if question['type'] == 'pattern':
        st.markdown("**Welche Form folgt in der Reihe?**")
        st.markdown(f"### {' → '.join(question['sequence'])} → ?")
        
    elif question['type'] == 'matrix':
        st.markdown("**Welche Form gehört in das Fragezeichen-Feld?**")
        # Matrix anzeigen
        matrix_html = "<div class='matrix-display'>"
        for row in question['matrix']:
            matrix_html += " ".join(row) + "<br>"
        matrix_html += "</div>"
        st.markdown(matrix_html, unsafe_allow_html=True)
        
    elif question['type'] == 'spatial' or question['type'] == 'folding':
        st.markdown(f"**{question['question']}**")
        
    elif question['type'] == 'number':
        st.markdown("**Setzen Sie die Zahlenreihe fort:**")
        st.markdown(f"### {' → '.join(map(str, question['sequence']))} → ?")
        
    elif question['type'] == 'logic':
        st.markdown("**Prämissen:**")
        for premise in question['premises']:
            st.markdown(f"- {premise}")
        st.markdown("**Welche Schlussfolgerung ist korrekt?**")
        question['options'] = question['conclusions']
    
    # Antwortoptionen
    if question['type'] == 'number':
        answer = st.number_input("Ihre Antwort:", step=1, key=f"answer_{index}")
    else:
        answer = st.radio(
            "Wählen Sie:",
            options=range(len(question['options'])),
            format_func=lambda x: question['options'][x],
            key=f"answer_{index}"
        )
    
    return answer

def main():
    """Hauptfunktion der Streamlit App"""
    
    st.title("⚖️ Justiz IQ-Training System")
    st.markdown("### Professionelle Vorbereitung auf den Einstellungstest")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Testeinstellungen")
        
        test_type = st.selectbox(
            "📚 Testbereich",
            ["Geometrische Muster", "Räumliches Denken", "Zahlenreihen", "Logik", "Gemischter Test"]
        )
        
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
        
        num_questions = st.slider("📝 Anzahl Fragen", 5, 20, 10)
        
        st.divider()
        
        if st.button("🚀 Test starten", type="primary", use_container_width=True):
            engine = TestEngine()
            st.session_state.current_test = engine.create_test(test_type, difficulty, num_questions)
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.test_history = []
            st.session_state.test_active = True
            st.session_state.show_result = False
            st.rerun()
        
        if st.button("🔄 Zurücksetzen", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Hauptbereich
    if not st.session_state.test_active:
        # Willkommensbildschirm
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **📊 Geometrische Muster**
            - Formensequenzen
            - Matrizen mit Symbolen
            - Transformationsregeln
            """)
            
            st.success("""
            **🎲 Räumliches Denken**
            - 3D-Rotationen
            - Würfelaufgaben
            - Papierfaltung
            """)
        
        with col2:
            st.warning("""
            **🔢 Zahlenreihen**
            - Arithmetische Folgen
            - Fibonacci-Muster
            - Komplexe Sequenzen
            """)
            
            st.error("""
            **🧠 Logik**
            - Syllogismen
            - Schlussfolgerungen
            - Prämissen-Analyse
            """)
        
        st.markdown("---")
        st.markdown("### 💡 Wählen Sie links einen Testbereich und starten Sie!")
        
    else:
        # Test läuft
        if st.session_state.current_question < len(st.session_state.current_test):
            # Progress bar
            progress = st.session_state.current_question / len(st.session_state.current_test)
            st.progress(progress)
            
            question = st.session_state.current_test[st.session_state.current_question]
            user_answer = display_question(question, st.session_state.current_question)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("✅ Antwort prüfen", type="primary", use_container_width=True):
                    # Antwort auswerten
                    correct = False
                    
                    if question['type'] == 'number':
                        correct = user_answer == question['answer']
                    else:
                        correct_idx = question.get('answer', question.get('correct', 0))
                        correct = user_answer == correct_idx
                    
                    st.session_state.test_history.append({
                        'question': st.session_state.current_question + 1,
                        'correct': correct,
                        'type': question['type']
                    })
                    
                    if correct:
                        st.session_state.score += 1
                    
                    st.session_state.show_result = True
                    st.rerun()
            
            # Ergebnis anzeigen
            if st.session_state.show_result:
                last_result = st.session_state.test_history[-1]
                
                if last_result['correct']:
                    st.success("✅ Richtig!")
                else:
                    st.error(f"❌ Falsch! Richtige Antwort: {question['answer']}")
                
                with st.expander("📚 Erklärung"):
                    st.info(question['explanation'])
                
                if st.button("Weiter →", type="primary"):
                    st.session_state.current_question += 1
                    st.session_state.show_result = False
                    st.rerun()
        
        else:
            # Test beendet
            st.balloons()
            st.success("🎉 Test abgeschlossen!")
            
            # Ergebnisse
            total = len(st.session_state.current_test)
            score = st.session_state.score
            percentage = (score / total) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Richtige Antworten", f"{score}/{total}")
            with col2:
                st.metric("Prozent", f"{percentage:.1f}%")
            with col3:
                if percentage >= 80:
                    st.metric("Bewertung", "Sehr gut! 🌟")
                elif percentage >= 60:
                    st.metric("Bewertung", "Gut! 👍")
                else:
                    st.metric("Bewertung", "Weiter üben! 💪")
            
            # Detaillierte Ergebnisse
            st.markdown("### 📊 Detaillierte Auswertung")
            df = pd.DataFrame(st.session_state.test_history)
            st.dataframe(df, use_container_width=True)
            
            if st.button("🔄 Neuer Test", type="primary"):
                st.session_state.test_active = False
                st.rerun()

if __name__ == "__main__":
    main()
