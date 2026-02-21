import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="School Performance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- PROFESSIONAL CSS ----------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141e30, #243b55);
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.1);
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
}
h1, h2, h3 {
    color: white !important;
}
.block-container {
    padding-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA GENERATION ----------------
@st.cache_data
def generate_data():
    np.random.seed(42)

    teachers = ["Mr. Sharma", "Ms. Patel", "Mr. Khan", "Ms. Iyer"]
    sections = ["A", "B", "C"]
    subjects = ["Math", "Science", "English"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

    student_names = ["Aman", "Riya", "Kabir", "Sneha", "Arjun",
                     "Priya", "Rahul", "Meera", "Ishaan", "Anaya"]

    data = []
    student_id = 1

    for month in months:
        for _ in range(50):
            data.append([
                student_id,
                random.choice(student_names),
                random.choice(teachers),
                random.choice(sections),
                random.choice(subjects),
                np.random.randint(40, 100),
                100,
                np.random.randint(18, 26),
                26,
                np.random.randint(0, 6),
                np.random.choice(["Yes", "No"], p=[0.1, 0.9]),
                month
            ])
            student_id += 1

    columns = ["student_id", "student_name", "teacher", "section",
               "subject", "score", "max_score",
               "attendance_days", "total_days",
               "late_count", "attrition", "month"]

    df = pd.DataFrame(data, columns=columns)

    df["performance_percent"] = (df["score"] / df["max_score"]) * 100
    df["attendance_percent"] = (df["attendance_days"] / df["total_days"]) * 100

    def risk_level(row):
        if row["performance_percent"] < 50 or row["attendance_percent"] < 60:
            return "High Risk"
        elif row["performance_percent"] < 70:
            return "Medium Risk"
        else:
            return "Low Risk"

    df["risk_level"] = df.apply(risk_level, axis=1)

    return df


data = generate_data()

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login():
    st.title("🔐 School Dashboard Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
        else:
            st.error("Invalid Credentials")


# ---------------- SIDEBAR FILTERS ----------------
def sidebar_filters(df):
    st.sidebar.title("🔎 Filters")

    teacher = st.sidebar.multiselect("Teacher", df["teacher"].unique(),
                                     default=df["teacher"].unique())

    section = st.sidebar.multiselect("Section", df["section"].unique(),
                                     default=df["section"].unique())

    month = st.sidebar.multiselect("Month", df["month"].unique(),
                                   default=df["month"].unique())

    filtered = df[
        (df["teacher"].isin(teacher)) &
        (df["section"].isin(section)) &
        (df["month"].isin(month))
    ]

    return filtered


# ---------------- MAIN DASHBOARD ----------------
def dashboard(df):
    st.title("📊 Overall Performance Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", df["student_id"].nunique())
    col2.metric("Average Score", round(df["score"].mean(), 2))
    col3.metric("Attendance %", round(df["attendance_percent"].mean(), 2))
    col4.metric("Attrition %", round((df["attrition"] == "Yes").mean() * 100, 2))

    st.markdown("---")

    colA, colB = st.columns(2)

    with colA:
        avg_attendance = round(df["attendance_percent"].mean(), 2)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_attendance,
            title={'text': "Avg Attendance %"},
            gauge={'axis': {'range': [0, 100]}}
        ))
        fig_gauge.update_layout(height=280)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with colB:
        risk_data = df["risk_level"].value_counts().reset_index()
        risk_data.columns = ["Risk Level", "Count"]

        fig_pie = px.pie(risk_data,
                         names="Risk Level",
                         values="Count",
                         color="Risk Level")
        fig_pie.update_layout(height=280)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    colC, colD = st.columns(2)

    with colC:
        monthly = df.groupby("month")["performance_percent"].mean().reset_index()
        fig_line = px.line(monthly, x="month", y="performance_percent", markers=True)
        fig_line.update_layout(height=320)
        st.plotly_chart(fig_line, use_container_width=True)

    with colD:
        teacher_perf = df.groupby("teacher")["score"].mean().reset_index()
        fig_bar = px.bar(teacher_perf, x="teacher", y="score", color="teacher")
        fig_bar.update_layout(height=320)
        st.plotly_chart(fig_bar, use_container_width=True)


# ---------------- TEACHER DASHBOARD ----------------
def teacher_dashboard(df):
    st.title("👩‍🏫 Teacher Dashboard")

    teacher = st.selectbox("Select Teacher", df["teacher"].unique())
    teacher_df = df[df["teacher"] == teacher]

    col1, col2 = st.columns(2)
    col1.metric("Avg Score", round(teacher_df["score"].mean(), 2))
    col2.metric("Attendance %", round(teacher_df["attendance_percent"].mean(), 2))

    subject_perf = teacher_df.groupby("subject")["score"].mean().reset_index()

    fig = px.bar(subject_perf, x="subject", y="score", color="subject")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detailed Data (Conditional Formatting)")

    styled = teacher_df.style.applymap(
        lambda x: "background-color: #FFCCCC"
        if isinstance(x, (int, float)) and x < 50 else "",
        subset=["score"]
    )

    st.dataframe(styled)


# ---------------- LATE & ATTRITION ----------------
def late_attrition_dashboard(df):
    st.title("⏰ Late Count & Attrition Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        late_data = df.groupby("section")["late_count"].sum().reset_index()
        fig_late = px.bar(late_data, x="section", y="late_count", color="section")
        st.plotly_chart(fig_late, use_container_width=True)

    with col2:
        attrition_data = df.groupby("teacher")["attrition"].apply(
            lambda x: (x == "Yes").sum()).reset_index(name="Attrition Count")

        fig_attr = px.bar(attrition_data, x="teacher",
                          y="Attrition Count", color="teacher")
        st.plotly_chart(fig_attr, use_container_width=True)


# ---------------- MAIN CONTROL ----------------
if not st.session_state.logged_in:
    login()
else:
    filtered_data = sidebar_filters(data)

    st.sidebar.markdown("### 📥 Export Data")
    csv = filtered_data.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("Download CSV",
                               csv,
                               "filtered_school_data.csv",
                               "text/csv")

    menu = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Teacher Dashboard", "Late & Attrition"]
    )

    if menu == "Dashboard":
        dashboard(filtered_data)
    elif menu == "Teacher Dashboard":
        teacher_dashboard(filtered_data)
    else:
        late_attrition_dashboard(filtered_data)