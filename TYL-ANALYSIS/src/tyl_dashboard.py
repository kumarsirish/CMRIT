import io

import pandas as pd
import streamlit as st

from tyl_analysis import (
    Skill,
    flatten_columns,
    rename_columns,
    find_column_by_contains,
    find_score_columns_by_suffix,
    get_filtered_df,
)


def process_sheet_for_ui(
    excel_bytes,
    sheet_name,
    skills,
    required_columns_below_passing_marks,
    column_rename_map,
):
    df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=sheet_name, header=[0, 1])
    df = flatten_columns(df)
    df = rename_columns(df, column_rename_map)

    email_col = find_column_by_contains(df, "Email")
    name_col = find_column_by_contains(df, "Name")

    results = {}
    for skill in skills:
        try:
            score_columns = find_score_columns_by_suffix(df, skill.score_suffix_patterns())
        except ValueError as err:
            results[skill.name] = {"error": str(err), "data": None}
            continue

        filtered_df = get_filtered_df(
            df.copy(),
            score_columns,
            skill.passing_marks,
            required_columns_below_passing_marks,
        )
        results[skill.name] = {
            "error": None,
            "score_columns": score_columns,
            "data": filtered_df[[email_col, name_col, *score_columns]],
        }

    return results


def style_below_passing(value, passing_marks):
    try:
        return "color: red; font-weight: 700;" if float(value) < float(passing_marks) else ""
    except (TypeError, ValueError):
        return ""


def center_styler(df):
    return df.style.set_properties(**{"text-align": "justify", "text-justify": "inter-word"}).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("text-align", "justify"),
                    ("text-justify", "inter-word"),
                    ("font-weight", "bold"),
                ],
            },
            {
                "selector": "td",
                "props": [("text-align", "justify"), ("text-justify", "inter-word")],
            },
        ]
    )


def render_tyl_analysis_dashboard():
    top_col1, top_col2 = st.columns([1, 6])
    with top_col1:
        if st.button("← Back to Home"):
            st.session_state["current_page"] = "home"
            st.rerun()

    with top_col2:
        st.title("TYL Analysis Dashboard")

    st.markdown("### TYL Eligibility")
    eligibility_df = pd.DataFrame(
        {
            "Final year": [4, 4, 5, "3.5 or 4", 3],
            "6th semester": [4, 3, 3, 3.5, 3],
            "4th semester": [3, 1, 2, 3, 2],
        },
        index=["Lx", "Ax", "Cx", "Px", "Sx"],
    )
    st.table(center_styler(eligibility_df))

    st.markdown("### TYL Marks Reference")
    marks_reference_df = pd.DataFrame(
        {
            "L1": [100, 65],
            "L2": [100, 65],
            "L3": [100, 70],
            "L4": [100, 70],
            "A1": [100, 50],
            "A2": [100, 50],
            "A3": [100, 50],
            "A4": [100, 65],
            "S1": [100, 50],
            "S2": [100, 50],
            "S3": [100, 50],
            "S4": [100, 50],
            "C2 Odd": [25, 10],
            "C2 Full": [25, 10],
            "C3 Odd": [100, 15],
            "C3 Full": [100, 25],
            "C4 Odd": [100, 50],
            "C4 Full": [100, 50],
            "C5 Full": [100, 50],
            "P1-C": [100, 50],
            "P2-Python": [100, 50],
            "P3-Python": [100, 60],
            "P3-Java": [100, 60],
            "P4-Programming part 1": [100, 70],
            "P4-Programming part 2": [100, 70],
            "P4-MAD/FSD": [100, 70],
            "P4-DS": [100, 70],
        },
        index=["Max marks", "Pass marks"],
    )
    st.table(center_styler(marks_reference_df))

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        passing_marks = st.number_input("Passing marks", min_value=0, max_value=100, value=50)
        required_below = st.number_input(
            "Subjects in which student scored below passing marks (e.g. 1 for at least 1 subject, 2 for at least 2 subjects, etc.)",
            min_value=1,
            max_value=4,
            value=1,
        )
    with col2:
        sheets_text = st.text_input("Sheets (comma separated)", "UG-AIML,UG-CSAIML")

    if st.button("Run Analysis"):
        skills = [
            Skill(name="Ax", score_suffixes=["A1", "A2", "A3"], passing_marks=int(passing_marks)),
            Skill(name="Sx", score_suffixes=["S1", "S2", "S3"], passing_marks=int(passing_marks)),
        ]
        passing_marks_by_skill = {skill.name: skill.passing_marks for skill in skills}

        column_rename_map = {
            "Full Name_As per PAN Card or 10th Mark scard": "Name",
        }

        sheet_names = [s.strip() for s in sheets_text.split(",") if s.strip()]

        if uploaded_file is None:
            st.error("Please upload an Excel file.")
            return
        excel_bytes = uploaded_file.getvalue()

        results_by_sheet = {}
        for sheet_name in sheet_names:
            try:
                results_by_sheet[sheet_name] = process_sheet_for_ui(
                    excel_bytes,
                    sheet_name,
                    skills,
                    int(required_below),
                    column_rename_map,
                )
            except Exception as err:
                results_by_sheet[sheet_name] = {"__sheet_error__": str(err)}

        for skill in skills:
            skill_name = skill.name
            st.markdown(f"## Skill {skill_name}")

            for sheet_name in sheet_names:
                st.subheader(f"Sheet: {sheet_name}")
                sheet_result = results_by_sheet.get(sheet_name, {})

                if "__sheet_error__" in sheet_result:
                    st.error(f"Failed to process {sheet_name}: {sheet_result['__sheet_error__']}")
                    continue

                details = sheet_result.get(skill_name)
                if not details:
                    st.warning(f"No data for {skill_name} in {sheet_name}")
                    continue

                if details["error"]:
                    st.warning(details["error"])
                    continue

                filtered_df = details["data"]
                st.write(f"Students matched: {len(filtered_df)}")
                score_columns = details["score_columns"]
                skill_passing_marks = passing_marks_by_skill.get(skill_name, int(passing_marks))
                styled_df = filtered_df.style.map(
                    lambda value: style_below_passing(value, skill_passing_marks),
                    subset=score_columns,
                ).set_properties(**{"text-align": "justify", "text-justify": "inter-word"}).set_table_styles(
                    [
                        {
                            "selector": "th",
                            "props": [
                                ("text-align", "justify"),
                                ("text-justify", "inter-word"),
                                ("font-weight", "bold"),
                            ],
                        },
                        {
                            "selector": "td",
                            "props": [("text-align", "justify"), ("text-justify", "inter-word")],
                        },
                    ]
                )
                st.dataframe(styled_df, use_container_width=True)

                red_count_data = {}
                for col in score_columns:
                    numeric_series = pd.to_numeric(filtered_df[col], errors="coerce")
                    red_count_data[col] = (numeric_series < skill_passing_marks).sum()

                red_count_df = pd.DataFrame([red_count_data], index=["Red count"])
                st.caption("Count of values below passing marks (red)")
                st.table(center_styler(red_count_df))

                csv_data = filtered_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Download {sheet_name}_{skill_name}.csv",
                    data=csv_data,
                    file_name=f"{sheet_name}_{skill_name}.csv",
                    mime="text/csv",
                )
