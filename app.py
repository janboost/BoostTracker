import sqlite3
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st

DB_FILE = "tasks.db"

# -------------------------
# DATABASE LAYER
# -------------------------
class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
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

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

# -------------------------
# TASK MANAGER
# -------------------------
class TaskManager:
    CATEGORIES = ["Productividad", "Estudio", "Fitness", "Hábitos"]
    PRIORITIES = ["Alta", "Media", "Baja"]

    def __init__(self):
        self.db = Database()

    def add_task(self, name, category, priority):
        if category not in self.CATEGORIES:
            raise ValueError("Categoría inválida")
        if priority not in self.PRIORITIES:
            raise ValueError("Prioridad inválida")

        task_id = str(uuid.uuid4())
        date = datetime.now().strftime("%Y-%m-%d")

        self.db.execute("""
            INSERT INTO tasks (id, name, category, priority, status, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, name, category, priority, 0, date))

    def get_tasks(self, date=None):
        if date:
            rows = self.db.fetchall("SELECT * FROM tasks WHERE date=?", (date,))
        else:
            rows = self.db.fetchall("SELECT * FROM tasks")
        return rows

    def update_status(self, task_id, status):
        self.db.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))

    def to_dataframe(self, rows):
        return pd.DataFrame(rows, columns=["id", "name", "category", "priority", "status", "date"])

    def metrics(self, df):
        if df.empty:
            return {"total": 0, "completed": 0, "pending": 0, "percent": 0}

        total = len(df)
        completed = df[df["status"] == 1].shape[0]
        pending = total - completed
        percent = (completed / total * 100) if total else 0

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "percent": percent
        }

    def streak(self, df, threshold=80):
        if df.empty:
            return 0

        streak = 0
        dates = sorted(df["date"].unique(), reverse=True)

        for d in dates:
            day_df = df[df["date"] == d]
            total = len(day_df)
            completed = day_df[day_df["status"] == 1].shape[0]

            if total == 0:
                continue

            percent = (completed / total) * 100
            if percent >= threshold:
                streak += 1
            else:
                break

        return streak

# -------------------------
# STREAMLIT UI
# -------------------------
tm = TaskManager()

st.set_page_config(page_title="Task Tracker", layout="wide")
st.title("📊 Advanced Task Tracker")

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Add Task", "Manage Tasks"])

date_filter = st.sidebar.date_input("Filter by date", datetime.now())
date_str = date_filter.strftime("%Y-%m-%d")

tasks = tm.get_tasks(date_str)
df = tm.to_dataframe(tasks)

# -------------------------
# DASHBOARD
# -------------------------
if menu == "Dashboard":
    st.subheader("📅 Daily Overview")

    metrics = tm.metrics(df)
    streak = tm.streak(tm.to_dataframe(tm.get_tasks()))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", metrics["total"])
    col2.metric("Completed", metrics["completed"])
    col3.metric("Pending", metrics["pending"])
    col4.metric("Completion %", f"{metrics['percent']:.1f}%")

    st.write(f"🔥 Streak: {streak} days")

    if not df.empty:
        chart_data = df.groupby("category")["status"].mean() * 100
        st.bar_chart(chart_data)

        st.subheader("Tasks")
        st.dataframe(df)
    else:
        st.info("No tasks for this date.")

# -------------------------
# ADD TASK
# -------------------------
elif menu == "Add Task":
    st.subheader("➕ Add New Task")

    name = st.text_input("Task name")
    category = st.selectbox("Category", tm.CATEGORIES)
    priority = st.selectbox("Priority", tm.PRIORITIES)

    if st.button("Add Task"):
        if name:
            tm.add_task(name, category, priority)
            st.success("Task added!")
        else:
            st.error("Task name required")

# -------------------------
# MANAGE TASKS
# -------------------------
elif menu == "Manage Tasks":
    st.subheader("🛠 Manage Tasks")

    if df.empty:
        st.info("No tasks to manage")
    else:
        for _, row in df.iterrows():
            cols = st.columns([4,2,2,2,2])
            cols[0].write(row["name"])
            cols[1].write(row["category"])
            cols[2].write(row["priority"])
            cols[3].write("✅" if row["status"] else "❌")

            if cols[4].button("Toggle", key=row["id"]):
                new_status = 0 if row["status"] == 1 else 1
                tm.update_status(row["id"], new_status)
                st.experimental_rerun()
