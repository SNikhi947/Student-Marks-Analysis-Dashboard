"""
Utilities for loading and processing student marks data.
"""

import io
from typing import List, Union
import pandas as pd
from pandas import DataFrame

DEFAULT_SAMPLE_PATH = "data/sample_marks.csv"

def load_data(path_or_buffer: Union[str, io.BytesIO]) -> DataFrame:
    """Load CSV into DataFrame and ensure StudentID + Name exist"""
    df = pd.read_csv(path_or_buffer)
    if "StudentID" not in df.columns:
        df.insert(0, "StudentID", range(1, len(df) + 1))
    if "Name" not in df.columns:
        df.insert(1, "Name", [f"Student {i}" for i in range(1, len(df) + 1)])
    df.columns = df.columns.str.strip()
    return df

def compute_student_aggregates(df: DataFrame, subject_cols: List[str], treat_missing_as_zero=True) -> DataFrame:
    """Compute Total, Percentage, and Grade for students"""
    df = df.copy()
    for s in subject_cols:
        if s not in df.columns:
            df[s] = 0.0
    if treat_missing_as_zero:
        marks = df[subject_cols].fillna(0.0)
        total = marks.sum(axis=1)
        max_total = 100 * len(subject_cols)
        percentage = total / max_total * 100
    else:
        total = df[subject_cols].sum(axis=1, skipna=True)
        counts = df[subject_cols].count(axis=1)
        percentage = total / (counts * 100) * 100
        percentage = percentage.fillna(0)
    df["Total"] = total.astype(int)
    df["Percentage"] = percentage.round(2)
    df["Grade"] = df["Percentage"].apply(grade_from_percentage)
    return df

def grade_from_percentage(pct: float) -> str:
    """Grade mapping from percentage"""
    try:
        pct = float(pct)
    except Exception:
        return "N/A"
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B+"
    if pct >= 60: return "B"
    if pct >= 50: return "C"
    if pct >= 40: return "D"
    return "F"

def compute_statistics(df: DataFrame) -> dict:
    """Compute overall KPIs (always returns the keys)"""
    if df.empty or "Percentage" not in df.columns:
        return {"avg": 0, "median": 0, "highest": 0, "pass_rate": 0}

    avg = df["Percentage"].mean()
    median = df["Percentage"].median()
    highest = df["Percentage"].max()
    pass_rate = (df["Percentage"] >= 40).mean() * 100

    return {
        "avg": round(avg, 2),
        "median": round(median, 2),
        "highest": round(highest, 2),
        "pass_rate": round(pass_rate, 2)
    }

def filter_data(df: DataFrame, sel_class="All", sel_section="All", min_percent=0, top_n=None) -> DataFrame:
    """Filter by class, section, min % and top N"""
    filtered = df.copy()
    if sel_class != "All" and "Class" in filtered.columns:
        filtered = filtered[filtered["Class"] == sel_class]
    if sel_section != "All" and "Section" in filtered.columns:
        filtered = filtered[filtered["Section"] == sel_section]
    if min_percent > 0 and "Percentage" in filtered.columns:
        filtered = filtered[filtered["Percentage"] >= min_percent]
    if top_n and "Percentage" in filtered.columns:
        filtered = filtered.sort_values(by="Percentage", ascending=False).head(int(top_n))
    return filtered

def export_data(df: DataFrame):
    """Return CSV + Excel bytes"""
    csv_data = df.to_csv(index=False).encode("utf-8")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Students")
    excel_data = output.getvalue()
    return csv_data, excel_data
