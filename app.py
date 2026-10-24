import streamlit as st
import os
import re
import math
import random
from openai import OpenAI

# ====================== НАСТРОЙКИ ======================
MATERIALS_FOLDER = "materials"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

MODEL = "meta-llama/llama-3.1-8b-instruct:free"

# ====================== ЗАГРУЗКА МАТЕРИАЛОВ ======================
def load_materials():
    materials = []
    if not os.path.exists(MATERIALS_FOLDER):
        return "Папка materials не найдена!"
    
    files = sorted([f for f in os.listdir(MATERIALS_FOLDER) if f.endswith(".txt")])
    for filename in files:
        path = os.path.join(MATERIALS_FOLDER, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    materials.append(f"=== {filename} ===\n{content}")
        except Exception as e:
            materials.append(f"=== {filename} ===\nОшибка чтения: {e}")
    return "\n\n".join(materials)

def clean_text(text):
    text = re.sub(r'\\\[|\\\]|\\\(|\\\)', '', text)
    text = re.sub(r'\\frac\s*\{([^}]*)\}\s*\{([^}]*)\}', r'(\1)/(\2)', text)
    text = text.replace('\\cdot', '*').replace('\\times', '*')
    text = text.replace('\\sqrt', 'sqrt').replace('\\pi', 'pi')
    text = text.replace('\\left', '').replace('\\right', '')
    text = text.replace('\\', '')
    text = text.replace('{', '').replace('}', '')
    text = text.replace('[', '').replace(']', '')
    text = re.sub(r' +', ' ', text)
    return text.strip()

lab_materials = load_materials()

QUESTIONS = [
    "Определите понятия момента инерции материальной точки и твёрдого тела относительно оси.",
    "Как рассчитываются моменты инерции тел правильной формы (например, стержня, диска, шара)?",
    "Когда возникает понятие тензора инерции?",
    "Что называется главными (центральными) осями инерции?",
    "Как связаны момент инерции и кинетическая энергия вращательного движения?",
    "Сформулируйте основное уравнение динамики вращательного движения.",
    "В чём заключается теорема Штейнера?",
    "Почему в эксперименте требуется набирать не менее 10 колебаний?",
    "Какой физический смысл имеет модуль кручения нити κ?",
    "Почему период крутильных колебаний не зависит от амплитуды при малых углах?",
    "Как по экспериментальным данным построить эллипсоид инерции?",
    "Что произойдёт с периодом колебаний, если момент инерции системы увеличить в 4 раза?",
    "Почему для определения момента инерции тела используется схема с пустой рамкой?",
    "Какие факторы могут привести к расхождению экспериментального и теоретического значений момента инерции?"
]

def get_special_answer(question):
    q = question.lower().replace("ё", "е")
    
    if any(word in q for word in ["рамк", "пустой рамк", "инерции рамк", "i_p", "iр"]):
        return """Момент инерции пустой рамки:

I_p = I_k * (T_p^2 / (T_kp^2 - T_p^2))

где:
- I_k — момент инерции куба
- T_p — период колебаний пустой рамки
- T_kp — период колебаний рамки с кубом"""

    if any(word in q for word in ["куб", "эталон", "инерции куб", "i_k", "iк"]):
        return """Момент инерции куба (эталонного тела):

I_k = (1/6) * m * a^2

где:
- m — масса куба
- a — длина ребра куба"""

    if any(word in q for word in ["исследуемого", "тела", "инерции тела", "i_t", "и_т", "параллелепипед"]):
        return """Момент инерции исследуемого тела:

I_t = I_p * ((T_tp^2 - T_p^2) / T_p^2)

где:
- I_p — момент инерции пустой рамки
- T_tp — период колебаний рамки с исследуемым телом
- T_p — период колебаний пустой рамки"""

    if any(word in q for word in ["эллипсоид", "осей эллипсоида", "длина осей", "полуосей"]):
        return """Длины полуосей эллипсоида инерции (в произвольном масштабе):

l_i = 1 / sqrt(I_i)

где I_i — момент инерции относительно соответствующей главной оси."""

    return None

SYSTEM_PROMPT = f"""
Ты — точный преподаватель физики.
Лабораторная работа: «Определение момента инерции твёрдых тел методом крутильных колебаний».

Материалы:
{lab_materials}

Строгие правила:
1. Формулы пиши ТОЛЬКО обычным текстом. Пример: I = (1/6) * m * a^2
2. Запрещено использовать LaTeX.
3. Отвечай коротко и только по материалам.
4. Если информации нет — прямо скажи.
5. Отвечай на русском языке.
"""

def ask_model(messages, temperature=0.2):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

def evaluate_answer(question, student_answer):
    prompt = f"""
Ты — лояльный преподаватель физики. Оценивай мягко. Важна суть ответа.

Вопрос: {question}
Ответ студента: {student_answer}

Верни ответ СТРОГО в формате:

ОЦЕНКА: число от 0 до 10
КОММЕНТАРИЙ: краткий комментарий
ПОДСКАЗКА: наводящий вопрос (НЕ повторяй исходный вопрос). Если оценка 7 и выше — напиши "нет"
"""
    text = ask_model([{"role": "user", "content": prompt}], temperature=0.3)
    
    score = 7
    comment = "Ответ принят"
    hint = "нет"
    
    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("ОЦЕНКА:"):
            try:
                score = int(re.search(r"\d+", line).group())
                score = max(0, min(10, score))
            except:
                score = 7
        elif line.upper().startswith("КОММЕНТАРИЙ:"):
            comment = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("ПОДСКАЗКА:"):
            hint = line.split(":", 1)[-1].strip()
    
    if hint.lower() == question.lower() or len(hint) < 15:
        hint = "Подумай, какие физические условия и законы лежат в основе этого явления."
    
    return score, comment, hint

def calculate_report_score(rel_errors):
    if not rel_errors:
        return 0
    big_errors = sum(1 for e in rel_errors if e >= 15)
    medium_errors = sum(1 for e in rel_errors if 5 <= e < 15)
    small_errors = sum(1 for e in rel_errors if 2 <= e < 5)
    
    score = 50
    score -= big_errors * 8
    score -= medium_errors * 3
    score -= small_errors * 1
    return max(15, score)

# ====================== ИНТЕРФЕЙС ======================
st.set_page_config(page_title="Преподаватель по физике", page_icon="Physics", layout="wide")
st.title("Преподаватель по лабораторной работе")
st.caption("Определение момента инерции твёрдых тел методом крутильных колебаний")

tab1, tab2, tab3 = st.tabs(["Чат с преподавателем", "Проверка отчёта", "Контрольные вопросы"])

# ---------- ЧАТ ----------
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])

    if prompt := st.chat_input("Задай вопрос по лабораторной..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            special = get_special_answer(prompt)
            if special:
                answer = special
                st.write(answer)
            else:
                with st.spinner("Думаю..."):
                    answer = clean_text(ask_model(st.session_state.messages))
                    st.write(answer)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})

# ---------- ПРОВЕРКА ОТЧЁТА ----------
with tab2:
    st.subheader("Проверка расчётов лабораторной работы")
    st.write("Введи данные и свои результаты. Оценка — из 50 баллов.")

    col1, col2 = st.columns(2)
    with col1:
        m = st.number_input("Масса куба m (кг)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="m")
        a = st.number_input("Ребро куба a (м)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="a")
    with col2:
        T_p = st.number_input("Период пустой рамки T_p (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="Tp")
        T_kp = st.number_input("Период рамки с кубом T_kp (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="Tkp")

    st.markdown("---")
    body_type = st.radio("Форма тела:", ["Параллелепипед", "Цилиндр"], horizontal=True)

    if body_type == "Параллелепипед":
        T1 = st.number_input("Период 1 — по высоте (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T1")
        T2 = st.number_input("Период 2 — по ширине (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T2")
        T3 = st.number_input("Период 3 — по главной диагонали (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T3")
        periods = [("По высоте", T1), ("По ширине", T2), ("По главной диагонали", T3)]
    else:
        T1 = st.number_input("Период 1 — по высоте (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T1c")
        T2 = st.number_input("Период 2 — по диаметру / ширине (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T2c")
        periods = [("По высоте", T1), ("По диаметру/ширине", T2)]

    st.markdown("---")
    st.markdown("### Твои результаты")
    student_Ik = st.number_input("Твой I_k", min_value=0.0, value=0.0, step=0.000001, format="%.6f", key="sIk")
    student_Ip = st.number_input("Твой I_p", min_value=0.0, value=0.0, step=0.000001, format="%.6f", key="sIp")

    student_Its = []
    student_ls = []
    for i, (name, _) in enumerate(periods):
        col_a, col_b = st.columns(2)
        with col_a:
            val_I = st.number_input(f"Твой I_t ({name})", min_value=0.0, value=0.0, step=0.000001, format="%.6f", key=f"sIt{i}")
            student_Its.append(val_I)
        with col_b:
            val_l = st.number_input(f"Твой l ({name})", min_value=0.0, value=0.0, step=0.0001, format="%.5f", key=f"sL{i}")
            student_ls.append(val_l)

    student_lk = st.number_input("Твой l для куба", min_value=0.0, value=0.0, step=0.0001, format="%.5f", key="sLk")

    if st.button("Проверить расчёты", type="primary"):
        if m <= 0 or a <= 0 or T_p <= 0 or T_kp <= 0 or student_Ik <= 0 or student_Ip <= 0:
            st.error("Заполни все обязательные поля.")
        else:
            I_k = (1/6) * m * (a ** 2)
            I_p = I_k * (T_p ** 2) / (T_kp ** 2 - T_p ** 2)
            l_k = 1 / math.sqrt(I_k)

            st.success("Расчёт выполнен")
            st.write(f"**I_k** = `{I_k:.6f}`")
            st.write(f"**I_p** = `{I_p:.6f}`")

            correct_Its, correct_ls, rel_errors = [], [], []
            rel_errors.append(abs(I_k - student_Ik) / I_k * 100)
            rel_errors.append(abs(I_p - student_Ip) / I_p * 100)

            for name, T_tp in periods:
                I_t = I_p * ((T_tp ** 2 - T_p ** 2) / T_p ** 2)
                l_t = 1 / math.sqrt(I_t)
                correct_Its.append(I_t)
                correct_ls.append(l_t)
                st.write(f"**I_t ({name})** = `{I_t:.6f}`")

            for i in range(len(periods)):
                rel_errors.append(abs(correct_Its[i] - student_Its[i]) / correct_Its[i] * 100)
                rel_errors.append(abs(correct_ls[i] - student_ls[i]) / correct_ls[i] * 100)
            rel_errors.append(abs(l_k - student_lk) / l_k * 100)

            st.write(f"**l куба** = `{l_k:.5f}`")
            for i, (name, _) in enumerate(periods):
                st.write(f"**l ({name})** = `{correct_ls[i]:.5f}`")

            report_score = calculate_report_score(rel_errors)
            st.session_state.report_score = report_score
            st.markdown(f"### Баллы за отчёт: **{report_score} / 50**")

# ---------- КОНТРОЛЬНЫЕ ВОПРОСЫ ----------
with tab3:
    st.subheader("Контрольные вопросы")
    st.write("5 вопросов. Максимум 50 баллов.")

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.quiz_questions = []
        st.session_state.current_q = 0
        st.session_state.scores = []
        st.session_state.finished = False
        st.session_state.waiting_hint = False
        st.session_state.last_hint = ""
        st.session_state.report_score = 0

    if not st.session_state.quiz_started:
        if st.button("Начать контрольные вопросы", type="primary"):
            st.session_state.quiz_started = True
            st.session_state.quiz_questions = random.sample(QUESTIONS, 5)
            st.session_state.current_q = 0
            st.session_state.scores = []
            st.session_state.finished = False
            st.session_state.waiting_hint = False
            st.rerun()
    else:
        if st.session_state.finished:
            questions_part = min(50, sum(st.session_state.scores))
            report_part = st.session_state.get("report_score", 0)
            final = report_part + questions_part
            st.success("Контроль завершён!")
            st.markdown(f"### Итоговая оценка: **{final} / 100**")
            st.write(f"• За отчёт: **{report_part} / 50**")
            st.write(f"• За вопросы: **{questions_part} / 50**")
            if st.button("Пройти ещё раз"):
                st.session_state.quiz_started = False
                st.rerun()
        else:
            q_index = st.session_state.current_q
            question = st.session_state.quiz_questions[q_index]
            st.markdown(f"**Вопрос {q_index + 1} из 5**")
            st.info(question)

            if st.session_state.waiting_hint:
                st.warning(f"Подсказка: {st.session_state.last_hint}")

            answer = st.text_area("Твой ответ:", key=f"ans_{q_index}")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.button("Ответить", type="primary")
            with col2:
                dont_know = st.button("Не знаю ответа")

            if submit or dont_know:
                if dont_know:
                    score, comment, hint = 0, "Ответ не дан", "нет"
                else:
                    if not answer.strip():
                        st.error("Напиши ответ.")
                        st.stop()
                    with st.spinner("Оцениваю..."):
                        score, comment, hint = evaluate_answer(question, answer)

                st.session_state.scores.append(score)
                st.write(f"Оценка: {score}/10 — {comment}")

                if len(st.session_state.scores) >= 5:
                    st.session_state.finished = True
                    st.rerun()
                else:
                    if score < 7 and hint.lower() != "нет" and not st.session_state.waiting_hint:
                        st.session_state.waiting_hint = True
                        st.session_state.last_hint = hint
                        st.session_state.scores.pop()
                        st.rerun()
                    else:
                        st.session_state.waiting_hint = False
                        st.session_state.current_q += 1
                        st.rerun()
