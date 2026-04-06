import sqlite3
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st

DB_FILE = "tasks.db"

# -------------------------
# DATABASE
# -------------------------
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            priority TEXT,
            status INTEGER,
            date TEXT
        )
        """)
        self.conn.commit()

    def execute(self, q, params=()):
        self.cursor.execute(q, params)
        self.conn.commit()

    def fetch(self, q, params=()):
        self.cursor.execute(q, params)
        return self.cursor.fetchall()


# -------------------------
# LOGIC
# -------------------------
class TaskManager:
    CATEGORIES = ["Productividad", "Estudio", "Fitness", "Hábitos"]
    PRIORITIES = ["Alta", "Media", "Baja"]

    def __init__(self):
        self.db = Database()

    def add_task(self, name, category, priority):
        task_id = str(uuid.uuid4())
        date = datetime.now().strftime("%Y-%m-%d")

        self.db.execute("""
        INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, name, category, priority, 0, date))

    def get_tasks(self, date=None):
        if date:
            return self.db.fetch("SELECT * FROM tasks WHERE date=?", (date,))
        return self.db.fetch("SELECT * FROM tasks")

    def update(self, task_id, status):
        self.db.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))

    def df(self, rows):
        return pd.DataFrame(rows, columns=["id","name","category","priority","status","date"])

    def metrics(self, df):
        if df.empty:
            return 0,0,0,0

        total = len(df)
        done = df[df["status"]==1].shape[0]
        pending = total - done
        percent = (done/total)*100

        return total, done, pending, percent

    def score(self, df):
        if df.empty:
            return 0

        score = 0
        for _, r in df.iterrows():
            if r["status"] == 1:
                if r["priority"] == "Alta":
                    score += 3
                elif r["priority"] == "Media":
                    score += 2
                else:
                    score += 1
        return score

    def streak(self):
        df = self.df(self.get_tasks())
        if df.empty:
            return 0

        streak = 0
        dates = sorted(df["date"].unique(), reverse=True)

        for d in dates:
            day = df[df["date"] == d]
            total = len(day)
            done = day[day["status"]==1].shape[0]

            if total == 0:
                continue

            percent = (done/total)*100

            if percent >= 80:
                streak += 1
            else:
                break

        return streak


# -------------------------
# UI STYLE
# -------------------------
st.set_page_config(page_title="BoostTracker", layout="wide")

st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
.metric { font-size:20px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

tm = TaskManager()

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🚀 BoostTracker")
menu = st.sidebar.radio("", ["Dashboard", "Añadir", "Gestionar"])

date = st.sidebar.date_input("Fecha", datetime.now())
date_str = date.strftime("%Y-%m-%d")

df = tm.df(tm.get_tasks(date_str))

# -------------------------
# DASHBOARD
# -------------------------
if menu == "Dashboard":

    st.title("📊 Dashboard")

    total, done, pending, percent = tm.metrics(df)
    score = tm.score(df)
    streak = tm.streak()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Hechas", done)
    c3.metric("Pendientes", pending)
    c4.metric("Cumplimiento", f"{percent:.0f}%")

    st.progress(percent/100)

    c5,c6 = st.columns(2)
    c5.metric("🔥 Racha", streak)
    c6.metric("🎯 Score", score)

    st.divider()

    if not df.empty:
        st.subheader("📈 Categorías")
        chart = df.groupby("category")["status"].mean()*100
        st.bar_chart(chart)

        st.subheader("📋 Tareas")

        df_show = df.copy()
        df_show["status"] = df_show["status"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df_show, use_container_width=True)
    else:
        st.info("No hay tareas hoy")

# -------------------------
# ADD
# -------------------------
elif menu == "Añadir":

    st.title("➕ Nueva tarea")

    with st.form("form"):
        name = st.text_input("Nombre")
        cat = st.selectbox("Categoría", tm.CATEGORIES)
        pri = st.selectbox("Prioridad", tm.PRIORITIES)

        ok = st.form_submit_button("Crear")

        if ok:
            if name:
                tm.add_task(name, cat, pri)
                st.success("Añadida")
                st.rerun()
            else:
                st.error("Falta nombre")

# -------------------------
# MANAGE
# -------------------------
elif menu == "Gestionar":

    st.title("🛠 Gestión")

    if df.empty:
        st.info("Sin tareas")
    else:
        for _, r in df.iterrows():
            col1,col2,col3,col4 = st.columns([4,2,2,2])

            col1.write(r["name"])
            col2.write(r["category"])
            col3.write(r["priority"])

            label = "✅" if r["status"] else "❌"
            if col4.button(label, key=r["id"]):
                tm.update(r["id"], 0 if r["status"] else 1)
                st.rerun()
