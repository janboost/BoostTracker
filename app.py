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
                
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Anime Boost Tracker", layout="wide")

# -------------------------
# STYLE (ANIME / SPORT THEME)
# -------------------------
st.markdown("""
<style>

/* Background */
body {
    background: radial-gradient(circle at top, #0b0f19, #020617);
    color: #e5e7eb;
    font-family: 'Segoe UI', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a, #020617);
}

/* Main container spacing */
.block-container {
    padding: 2rem 2.5rem;
}

/* Titles */
h1, h2, h3 {
    color: #f8fafc;
    font-weight: 700;
}

/* Cards */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 6px 25px rgba(0,0,0,0.5);
    transition: transform 0.2s ease;
}

.card:hover {
    transform: translateY(-4px);
    border: 1px solid #ef4444;
}

/* Metric title */
.metric-title {
    font-size: 13px;
    color: #9ca3af;
    letter-spacing: 1px;
}

/* Metric value */
.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: #f43f5e;
}

/* Buttons */
div.stButton > button {
    background: linear-gradient(90deg, #ef4444, #3b82f6);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.4rem 1rem;
    font-weight: bold;
}

div.stButton > button:hover {
    opacity: 0.9;
}

/* Divider */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #ef4444, transparent);
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🔥 Anime Tracker")

menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "⚔️ Tasks", "➕ Add Task"]
)

st.sidebar.divider()

date = st.sidebar.date_input("Date", datetime.now())
date_str = date.strftime("%Y-%m-%d")

# -------------------------
# CARD COMPONENT
# -------------------------
def card(title, value):
    st.markdown(f"""
    <div class="card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------
# DASHBOARD
# -------------------------
if menu == "🏠 Dashboard":

    st.title("⚡ Performance Dashboard")

    total, done, pending, percent = tm.metrics(df)
    score = tm.score(df)
    streak = tm.streak()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card("TOTAL", total)

    with c2:
        card("COMPLETED", done)

    with c3:
        card("PENDING", pending)

    with c4:
        card("COMPLIANCE", f"{percent:.0f}%")

    st.progress(percent / 100)

    st.write("")

    c5, c6 = st.columns(2)

    with c5:
        card("🔥 STREAK", streak)

    with c6:
        card("🎯 SCORE", score)

    st.divider()

    st.subheader("📊 Category Power")

    if not df.empty:
        chart = df.groupby("category")["status"].mean() * 100
        st.bar_chart(chart)

    st.subheader("📋 Task Overview")

    if not df.empty:
        df_show = df.copy()
        df_show["status"] = df_show["status"].map({0: "❌", 1: "✅"})
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.info("No tasks yet")

# -------------------------
# TASK MANAGEMENT
# -------------------------
elif menu == "⚔️ Tasks":

    st.title("⚔️ Manage Tasks")

    if df.empty:
        st.warning("No tasks available")
    else:
        edited_df = df.copy()
        edited_df["status"] = edited_df["status"].astype(bool)

        edited = st.data_editor(
            edited_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "status": st.column_config.CheckboxColumn("Done"),
                "priority": st.column_config.SelectboxColumn(
                    "Priority",
                    options=["Alta", "Media", "Baja"]
                )
            }
        )

        if st.button("💾 Save Changes"):
            for _, row in edited.iterrows():
                tm.update(row["id"], int(row["status"]))
            st.success("Updated")
            st.rerun()

# -------------------------
# ADD TASK
# -------------------------
elif menu == "➕ Add Task":

    st.title("➕ Create New Task")

    with st.form("form"):
        name = st.text_input("Task name")
        category = st.selectbox("Category", tm.CATEGORIES)
        priority = st.selectbox("Priority", tm.PRIORITIES)

        submitted = st.form_submit_button("Create")

        if submitted:
            if name.strip() == "":
                st.error("Name cannot be empty")
            else:
                tm.add_task(name, category, priority)
                st.success("Task created")
                st.rerun()
