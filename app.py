import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_utils import load_data, compute_statistics, filter_data, export_data

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Student Marks Analysis Dashboard",
    page_icon="🎓",
    layout="wide"
)

# ---- HEADER ----
st.markdown(
    """
    <div style="text-align:center; padding:15px 0;">
        <h1 style="margin-bottom:0; color:#2c3e50;">🎓 Student Marks Analysis Dashboard</h1>
        <p style="margin-top:8px; color:#7f8c8d; font-size:18px;">
            Interactive dashboard to explore student performance, statistics, and trends 📊
        </p>
        <hr style="border:1px solid #ddd; margin-top:10px; margin-bottom:20px;">
    </div>
    """,
    unsafe_allow_html=True
)

# ---- SIDEBAR ----
st.sidebar.header("📂 Data / Filters")
uploaded_file = st.sidebar.file_uploader("Upload marks CSV or Excel", type=["csv", "xlsx"])

# Load sample data or uploaded file
if st.sidebar.button("📥 Load sample data"):
    df = load_data("data/sample_marks.csv")
    st.session_state["data"] = df
    st.sidebar.success("✅ Sample data loaded.")
elif uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = load_data(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    st.session_state["data"] = df

df = st.session_state.get("data")

if df is None:
    st.warning("👆 Upload a CSV or Excel file, or load sample data from the sidebar.")
    st.stop()

# ---- PROCESS DATA ----
# Only numeric subject columns for charts (exclude Total, Percentage, StudentID, Class)
subject_cols = [c for c in df.select_dtypes(include="number").columns 
                if c not in ["Total", "Percentage", "StudentID"]]

if len(subject_cols) == 0:
    st.error("No numeric subject columns detected. Please upload a CSV/Excel with marks as numbers.")
    st.stop()

df["Total"] = df[subject_cols].sum(axis=1)
df["Percentage"] = df["Total"] / (len(subject_cols) * 100) * 100

# ---- FILTERS ----
class_options = ["All"] + sorted(df["Class"].unique().tolist()) if "Class" in df.columns else ["All"]
section_options = ["All"] + sorted(df["Section"].unique().tolist()) if "Section" in df.columns else ["All"]

sel_class = st.sidebar.selectbox("🏫 Select Class", class_options) if "Class" in df.columns else "All"
sel_section = st.sidebar.selectbox("🧑‍🤝‍🧑 Select Section", section_options) if "Section" in df.columns else "All"
min_percent = st.sidebar.slider("📉 Minimum Percentage", 0, 100, 0)
top_n = st.sidebar.number_input("🏆 Show Top N Students", 1, len(df), 5)

df_filtered = filter_data(df, sel_class, sel_section, min_percent, top_n)

# ---- KPIs ----
stats = compute_statistics(df_filtered)

st.markdown("## 📌 Key Performance Indicators")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Average %", f"{stats['avg']:.2f}")
with kpi2:
    st.metric("Median %", f"{stats['median']:.2f}")
with kpi3:
    st.metric("Highest %", f"{stats['highest']:.2f}")
with kpi4:
    st.metric("Pass Rate", f"{stats['pass_rate']:.1f}%")

st.markdown("---")

# ---- CHARTS ----
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Subject-wise Average Marks")
    avg_df = df_filtered[subject_cols].mean().reset_index()
    avg_df.columns = ["Subject", "Average Marks"]
    avg_chart = px.bar(
        avg_df,
        x="Subject",
        y="Average Marks",
        color="Average Marks",
        color_continuous_scale="Blues",
        labels={"Average Marks": "Average Marks"}
    )
    st.plotly_chart(avg_chart, use_container_width=True)

    st.subheader("📈 Percentage Distribution")
    hist_chart = px.histogram(
        df_filtered, x="Percentage", nbins=10,
        color_discrete_sequence=["#3498db"]
    )
    st.plotly_chart(hist_chart, use_container_width=True)

with col2:
    st.subheader("📦 Boxplot of Marks")
    box_df = df_filtered[subject_cols].melt(var_name="Subject", value_name="Marks")
    box_chart = px.box(
        box_df,
        x="Subject",
        y="Marks",
        points="all",
        color_discrete_sequence=["#2ecc71"]
    )
    st.plotly_chart(box_chart, use_container_width=True)

    st.subheader("🔗 Subject Correlation Heatmap")
    corr = df_filtered[subject_cols].corr()
    heatmap = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns, colorscale="Blues"
    ))
    heatmap.update_layout(margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(heatmap, use_container_width=True)

# ---- TOP STUDENTS ----
st.subheader("🏆 Top Students")
top_cols = ["Name", "Section", "Percentage", "Total"]
if "StudentID" in df_filtered.columns:
    top_cols.insert(0, "StudentID")
if "Class" in df_filtered.columns:
    top_cols.insert(1, "Class")

st.dataframe(
    df_filtered[top_cols].sort_values(by="Percentage", ascending=False).head(top_n),
    use_container_width=True
)

# ---- STUDENT DETAIL VIEW ----
st.markdown("## 👤 Student Detail View")
student_sel = st.selectbox("🔍 Select a student", df_filtered["Name"].unique())

if student_sel:
    student_data = df_filtered[df_filtered["Name"] == student_sel].iloc[0]

    st.markdown(
        f"""
        **🧑 Name:** {student_data['Name']}  
        **🏫 Class:** {student_data.get('Class', 'N/A')}  
        **📌 Section:** {student_data.get('Section', 'N/A')}  
        **📊 Total Marks:** {student_data['Total']}  
        **📈 Percentage:** {student_data['Percentage']:.2f}%  
        **🎯 Grade:** {student_data.get('Grade', 'N/A')}  
        """
    )

    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=student_data[subject_cols].values,
        theta=subject_cols,
        fill="toself",
        name=student_sel,
        marker=dict(color="#e74c3c")
    ))
    radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=30, r=30, t=30, b=30)
    )
    st.plotly_chart(radar, use_container_width=True)

# ---- EXPORT ----
st.markdown("## ⬇️ Export Data")
csv_data, excel_data = export_data(df_filtered)

col_csv, col_excel = st.columns(2)
with col_csv:
    st.download_button("📥 Download CSV", csv_data, file_name="students_filtered.csv", mime="text/csv")
with col_excel:
    st.download_button("📥 Download Excel", excel_data, file_name="students_filtered.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
