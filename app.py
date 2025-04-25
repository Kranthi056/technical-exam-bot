%%writefile app.py
import streamlit as st
import json
import re
import random
import time
from datetime import timedelta
from difflib import SequenceMatcher
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(page_title="Smart Technical Exam", layout="centered")

# CSS Styling
st.markdown("""
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f4f7fc;
            color: #333;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTextInput input {
            border-radius: 5px;
            border: 1px solid #ccc;
            padding: 10px;
        }
        .stSelectbox, .stRadio {
            font-size: 16px;
            padding: 10px;
            border-radius: 5px;
            background-color: #fff;
            border: 1px solid #ddd;
        }
        .stSelectbox option, .stRadio label {
            font-size: 16px;
        }
        .stForm {
            padding: 30px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .stForm h2 {
            text-align: center;
            color: #333;
        }
        .stForm p {
            font-size: 16px;
            color: #777;
        }
        .stForm input[type="text"], .stForm select {
            width: 100%;
            margin-bottom: 15px;
        }
        .stRadio>div, .stRadio>div>label {
            font-size: 16px;
        }
        .stInfo {
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 5px solid #4CAF50;
        }
        .stWarning {
            padding: 20px;
            background-color: #fff3cd;
            border-left: 5px solid #f39c12;
        }
        .stSuccess {
            padding: 20px;
            background-color: #d4edda;
            border-left: 5px solid #28a745;
        }
        .stError {
            padding: 20px;
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
        }
        .question-card {
            margin-bottom: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .question-card h5 {
            color: #4CAF50;
        }
        .stHeader {
            font-size: 28px;
            font-weight: bold;
            color: #333;
            text-align: center;
            margin-bottom: 20px;
        }
        .stMarkdown {
            font-size: 18px;
            color: #555;
        }
        .result-card {
            padding: 20px;
            background-color: #28a745;
            color: white;
            border-radius: 10px;
            text-align: center;
        }
        .result-card-fail {
            padding: 20px;
            background-color: #dc3545;
            color: white;
            border-radius: 10px;
            text-align: center;
        }
        .exam-timer {
            font-size: 18px;
            color: #333;
            font-weight: bold;
            text-align: center;
        }
        .question-list {
            margin-left: 50px;
        }
    </style>
""", unsafe_allow_html=True)

# Load Questions from File
def load_questions(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data["questions"] if "questions" in data else data

# Question Data
python_qs = load_questions("python.json")
sql_qs = load_questions("sql.json")
html_qs = load_questions("html.json")

# Email Validation
def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Smart Evaluation Logic
def smart_match(ans1, ans2):
    # If any of the answers are None or empty, treat them as invalid
    if ans1 is None or ans2 is None:
        return False
    
    # Compare text similarity
    ratio = SequenceMatcher(None, ans1.strip().lower(), ans2.strip().lower()).ratio()
    return ratio >= 0.85

def evaluate(questions, user_answers, role):
    score = 0
    topic_scores = {"Python": 0, "SQL": 0, "HTML": 0}
    wrong_questions = []

    for i, q in enumerate(questions):
        correct_raw = q["answer"]
        user_ans = user_answers.get(i, "")

        # For Python: decode 'a'/'b'/'c'/'d' to option text
        if role == "Data Analyst" and correct_raw in ['a', 'b', 'c', 'd']:
            idx = ord(correct_raw.lower()) - 97
            correct_option = q["options"][idx]
        else:
            correct_option = correct_raw

        if smart_match(user_ans, correct_option):
            score += 1
            if "Python" in q["question"]:
                topic_scores["Python"] += 1
            elif "SQL" in q["question"]:
                topic_scores["SQL"] += 1
            elif "HTML" in q["question"]:
                topic_scores["HTML"] += 1
        else:
            wrong_questions.append(f"Q{i+1}: {q['question']} - Your answer: {user_ans}, Correct answer: {correct_option}")
    
    return score, topic_scores, wrong_questions

# Plotting Function for Topic Analysis
def plot_topic_analysis(topic_scores, total_questions):
    labels = list(topic_scores.keys())
    values = list(topic_scores.values())
    
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=['#4CAF50', '#2196F3', '#FF9800'])
    ax.set_xlabel('Topics')
    ax.set_ylabel('Score')
    ax.set_title('Topic-wise Performance')
    ax.set_ylim([0, total_questions])
    
    st.pyplot(fig)

# Main App Setup
st.title("🧠 Smart Technical Exam Bot")

# Session State Initialization
if "exam_started" not in st.session_state:
    st.session_state.exam_started = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# Step-by-step Input Form
if not st.session_state.exam_started:
    with st.form("user_details"):
        name = st.text_input("Enter your name:")
        email = st.text_input("Enter your email:")
        role = st.selectbox("Select role:", ["Data Analyst", "Web Developer"])
        experience = st.selectbox("Experience:", ["0-2", "2-5"])
        submitted = st.form_submit_button("Start Exam")

        if submitted:
            if not valid_email(email):
                st.error("❌ Invalid email format!")
            else:
                st.session_state.name = name
                st.session_state.email = email
                st.session_state.role = role
                st.session_state.experience = experience
                st.session_state.user_answers = {}

                # Assign Questions and Timer
                if role == "Data Analyst":
                    st.session_state.duration = 30 * 60
                    py_qs = random.sample(python_qs, min(15, len(python_qs)))
                    sql_qs_sample = random.sample(sql_qs, min(15, len(sql_qs)))
                    st.session_state.questions = py_qs + sql_qs_sample
                else:
                    if experience == "0-2":
                        st.session_state.duration = 15 * 60
                        html_qs_sample = random.sample(html_qs, min(20, len(html_qs)))
                    else:
                        st.session_state.duration = 35 * 60
                        html_qs_sample = random.sample(html_qs, min(40, len(html_qs)))
                    st.session_state.questions = html_qs_sample

                random.shuffle(st.session_state.questions)
                st.session_state.start_time = time.time()
                st.session_state.exam_started = True
                st.rerun()

# Exam Interface
if st.session_state.exam_started:
    elapsed = time.time() - st.session_state.start_time
    remaining = st.session_state.duration - elapsed

    if remaining <= 0:
        st.warning("⏰ Time's up! Submitting your answers.")
        submit = True
    else:
        submit = False
        st.subheader(f"Time remaining: {str(timedelta(seconds=remaining))}")

    for i, q in enumerate(st.session_state.questions):
        answer = st.radio(q['question'], q['options'], key=i, index=None)
        st.session_state.user_answers[i] = answer

    if st.button("Submit Exam") or submit:
        score, topic_scores, wrong_questions = evaluate(
            st.session_state.questions, 
            st.session_state.user_answers, 
            st.session_state.role
        )
        
        # Display Results
        if score >= len(st.session_state.questions) * 0.6:
            st.success(f"🎉 You passed! Your score is {score}/{len(st.session_state.questions)}.")
            if wrong_questions:
                st.markdown("### Mistaken Questions:")
                for q in wrong_questions:
                    st.markdown(q)
        else:
            st.result_card_fail = f"❌ You failed! Your score is {score}/{len(st.session_state.questions)}."
            st.warning(f"Your score is {score}/{len(st.session_state.questions)}. Check your answers.")
            
        # Display Topic-wise Graph
        plot_topic_analysis(topic_scores, len(st.session_state.questions))
        
        # Additional Analysis and Suggestions based on wrong answers
        st.info("### Areas of Improvement")
        for wrong in wrong_questions:
            st.warning(f"Review the question: {wrong}")
