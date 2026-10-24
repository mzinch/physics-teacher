import streamlit as st
import ollama
import os
import re
import math
import random

MATERIALS_FOLDER = r"C:\physics_teacher\lab_1_moment_inercii\materials"

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

def evaluate_answer(question, student_answer):
    prompt = f"""
Ты — лояльный преподаватель физики. Оценивай мягко. Важна суть ответа, а не точные формулировки.
Даже если ответ неполный, но по смыслу верный — ставь высокую оценку.

Вопрос: {question}
Ответ студента: {student_answer}

Верни ответ СТРОГО в формате:

ОЦЕНКА: число от 0 до 10
КОММЕНТАРИЙ: краткий комментарий
ПОДСКАЗКА: наводящий вопрос (НЕ повторяй исходный вопрос). Если оценка 7 и выше — напиши "нет"
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.25}
    )
    
    text = response["message"]["content"]
    
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
    """Мягкая оценка из 50 баллов.
    Одна ошибка не должна сильно ронять баллы."""
    if not rel_errors:
        return 0
    
    # Считаем, сколько значений имеют большую ошибку
    big_errors = sum(1 for e in rel_errors if e >= 15)
    medium_errors = sum(1 for e in rel_errors if 5 <= e < 15)
    small_errors = sum(1 for e in rel_errors if 2 <= e < 5)
    
    score = 50
    score -= big_errors * 8          # серьёзная ошибка -8
    score -= medium_errors * 3       # средняя ошибка -3
    score -= small_errors * 1        # мелкая ошибка -1
    
    return max(15, score)  # минимум 15 баллов, если хоть что-то введено

st.set_page_config(page_title="Преподаватель по физике", page_icon="Physics", layout="wide")
st.title("Преподаватель по лабораторной работе")
st.caption("Определение момента инерции твёрдых тел методом крутильных колебаний")

tab1, tab2, tab3 = st.tabs(["Чат с преподавателем", "Проверка отчёта", "Контрольные вопросы"])

# ====================== ВКЛАДКА 1: ЧАТ ======================
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
                    response = ollama.chat(
                        model="qwen2.5:7b",
                        messages=st.session_state.messages,
                        options={"temperature": 0.1}
                    )
                    answer = clean_text(response["message"]["content"])
                    st.write(answer)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})

# ====================== ВКЛАДКА 2: ПРОВЕРКА ОТЧЁТА ======================
with tab2:
    st.subheader("Проверка расчётов лабораторной работы")
    st.write("Введи данные и свои результаты. Оценка — из 50 баллов (мелкие погрешности почти не штрафуются).")

    st.markdown("### 1. Эталонный куб и периоды рамки")
    col1, col2 = st.columns(2)

    with col1:
        m = st.number_input("Масса куба m (кг)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="m")
        a = st.number_input("Ребро куба a (м)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="a")

    with col2:
        T_p = st.number_input("Период пустой рамки T_p (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="Tp")
        T_kp = st.number_input("Период рамки с кубом T_kp (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="Tkp")

    st.markdown("---")
    st.markdown("### 2. Выбери форму исследуемого тела")
    body_type = st.radio("Форма тела:", ["Параллелепипед", "Цилиндр"], horizontal=True)

    st.markdown("### 3. Периоды колебаний с исследуемым телом")

    if body_type == "Параллелепипед":
        st.info("Для параллелепипеда делают 3 замера.")
        T1 = st.number_input("Период 1 — по высоте (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T1")
        T2 = st.number_input("Период 2 — по ширине (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T2")
        T3 = st.number_input("Период 3 — по главной диагонали (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T3")
        periods = [("По высоте", T1), ("По ширине", T2), ("По главной диагонали", T3)]
    else:
        st.info("Для цилиндра делают 2 замера.")
        T1 = st.number_input("Период 1 — по высоте (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T1c")
        T2 = st.number_input("Период 2 — по диаметру / ширине (с)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="T2c")
        periods = [("По высоте", T1), ("По диаметру/ширине", T2)]

    st.markdown("---")
    st.markdown("### 4. Твои рассчитанные результаты (обязательно)")

    student_Ik = st.number_input("Твой I_k (кг·м²)", min_value=0.0, value=0.0, step=0.000001, format="%.6f", key="sIk")
    student_Ip = st.number_input("Твой I_p (кг·м²)", min_value=0.0, value=0.0, step=0.000001, format="%.6f", key="sIp")

    student_Its = []
    student_ls = []

    st.write("Моменты инерции и длины осей эллипсоида:")

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
        errors = []
        if m <= 0 or a <= 0:
            errors.append("Введи массу и ребро куба.")
        if T_p <= 0 or T_kp <= 0:
            errors.append("Введи периоды пустой рамки и рамки с кубом.")
        if T_kp <= T_p:
            errors.append("Период с кубом должен быть больше периода пустой рамки.")
        if student_Ik <= 0 or student_Ip <= 0:
            errors.append("Обязательно введи свои I_k и I_p.")
        if any(t <= 0 for _, t in periods):
            errors.append("Введи все периоды для исследуемого тела.")
        if any(v <= 0 for v in student_Its) or any(v <= 0 for v in student_ls) or student_lk <= 0:
            errors.append("Обязательно введи все свои значения I_t и l.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            I_k = (1/6) * m * (a ** 2)
            I_p = I_k * (T_p ** 2) / (T_kp ** 2 - T_p ** 2)
            l_k = 1 / math.sqrt(I_k)

            st.success("Расчёт выполнен")
            st.markdown("### Правильные значения:")

            st.write(f"**I_k (куб)** = `{I_k:.6f}` кг·м²")
            st.write(f"**I_p (рамка)** = `{I_p:.6f}` кг·м²")

            correct_Its = []
            correct_ls = []
            rel_errors = []

            rel_errors.append(abs(I_k - student_Ik) / I_k * 100 if I_k != 0 else 100)
            rel_errors.append(abs(I_p - student_Ip) / I_p * 100 if I_p != 0 else 100)

            for name, T_tp in periods:
                I_t = I_p * ((T_tp ** 2 - T_p ** 2) / (T_p ** 2))
                l_t = 1 / math.sqrt(I_t)
                correct_Its.append(I_t)
                correct_ls.append(l_t)
                st.write(f"**I_t ({name})** = `{I_t:.6f}` кг·м²")

            for i in range(len(periods)):
                rel_errors.append(abs(correct_Its[i] - student_Its[i]) / correct_Its[i] * 100 if correct_Its[i] != 0 else 100)
                rel_errors.append(abs(correct_ls[i] - student_ls[i]) / correct_ls[i] * 100 if correct_ls[i] != 0 else 100)

            rel_errors.append(abs(l_k - student_lk) / l_k * 100 if l_k != 0 else 100)

            st.markdown("### Длины осей эллипсоида:")
            st.write(f"**l для куба** = `{l_k:.5f}`")
            for i, (name, _) in enumerate(periods):
                st.write(f"**l ({name})** = `{correct_ls[i]:.5f}`")

            st.markdown("---")
            st.markdown("### Сравнение с твоими результатами:")

            def compare(name, correct, student):
                diff = abs(correct - student)
                rel = (diff / correct) * 100 if correct != 0 else 0
                if rel < 3:
                    st.success(f"**{name}**: отлично (расхождение {rel:.1f}%)")
                elif rel < 10:
                    st.warning(f"**{name}**: небольшое расхождение ({rel:.1f}%)")
                else:
                    st.error(f"**{name}**: значительное расхождение ({rel:.1f}%)")

            compare("I_k", I_k, student_Ik)
            compare("I_p", I_p, student_Ip)
            for i, (name, _) in enumerate(periods):
                compare(f"I_t ({name})", correct_Its[i], student_Its[i])
                compare(f"l ({name})", correct_ls[i], student_ls[i])
            compare("l куба", l_k, student_lk)

            report_score = calculate_report_score(rel_errors)
            st.session_state.report_score = report_score

            st.markdown("---")
            st.markdown(f"### Баллы за проверку отчёта: **{report_score} / 50**")

# ====================== ВКЛАДКА 3: КОНТРОЛЬНЫЕ ВОПРОСЫ ======================
with tab3:
    st.subheader("Контрольные вопросы")
    st.write("Система задаст 5 вопросов. Максимум за эту часть — 50 баллов.")

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
            st.session_state.quiz_questions = random.sample(QUESTIONS, 5)  # всегда 5 вопросов
            st.session_state.current_q = 0
            st.session_state.scores = []
            st.session_state.finished = False
            st.session_state.waiting_hint = False
            st.rerun()
    else:
        if st.session_state.finished:
            # 5 вопросов × 10 баллов = 50 максимум
            questions_score = sum(st.session_state.scores)
            questions_part = min(50, int(questions_score / 50 * 50))  # просто сумма, т.к. максимум 50
            
            report_part = st.session_state.get("report_score", 0)
            final = report_part + questions_part

            st.success("Контроль завершён!")
            st.markdown(f"### Итоговая оценка: **{final} / 100**")
            st.write(f"• За проверку отчёта: **{report_part} / 50**")
            st.write(f"• За контрольные вопросы: **{questions_part} / 50**")
            
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
                st.write("Попробуй ответить ещё раз с учётом подсказки.")

            answer = st.text_area("Твой ответ:", key=f"answer_{q_index}")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.button("Ответить", type="primary")
            with col2:
                dont_know = st.button("Не знаю ответа")

            if submit or dont_know:
                if dont_know:
                    score = 0
                    comment = "Ответ не дан"
                    hint = "нет"
                else:
                    if not answer.strip():
                        st.error("Напиши ответ или нажми «Не знаю ответа».")
                        st.stop()
                    with st.spinner("Оцениваю ответ..."):
                        score, comment, hint = evaluate_answer(question, answer)

                st.session_state.scores.append(score)
                st.write(f"**Оценка за вопрос:** {score}/10")
                st.write(f"**Комментарий:** {comment}")

                if len(st.session_state.scores) >= 5:
                    st.session_state.finished = True
                    st.rerun()
                else:
                    if score < 7 and hint.lower() != "нет" and not st.session_state.waiting_hint:
                        st.session_state.waiting_hint = True
                        st.session_state.last_hint = hint
                        # не переходим к следующему вопросу, даём шанс исправить
                        st.session_state.scores.pop()  # убираем текущую оценку, чтобы можно было ответить ещё раз
                        st.rerun()
                    else:
                        st.session_state.waiting_hint = False
                        st.session_state.current_q += 1
                        st.rerun()