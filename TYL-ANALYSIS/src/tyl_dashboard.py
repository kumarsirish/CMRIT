import io
from pathlib import Path

import pandas as pd
import streamlit as st

from tyl_analysis import (
    Skill,
    flatten_columns,
    rename_columns,
    find_column_by_contains,
    find_score_columns_by_suffix,
    get_filtered_df,
    get_threshold_for_column,
)

# Pass marks per assessment, sourced from TYL Marks Reference table.
PASS_MARKS_REFERENCE = {
    "L1": 65, "L2": 65, "L3": 70, "L4": 70,
    "A1": 50, "A2": 50, "A3": 50, "A4": 65,
    "S1": 50, "S2": 50, "S3": 50, "S4": 50,
    "C2 Odd": 10, "C2 Full": 10, "C3 Odd": 15, "C3 Full": 25,
    "C4 Odd": 50, "C4 Full": 50, "C5 Full": 50,
    "P1-C": 50, "P2-Python": 50, "P3-Python": 60, "P3-Java": 60,
    "P4-Programming part 1": 70, "P4-Programming part 2": 70,
    "P4-MAD/FSD": 70, "P4-DS": 70,
}

EXCLUDED_STUDENTS_FILES = {
    "4th Semester": Path(__file__).resolve().parents[1] / "config" / "excluded_students_batch_2024_2028.csv",
    "6th Semester": Path(__file__).resolve().parents[1] / "config" / "excluded_students_batch_2023_2027.csv",
    "Final Year": Path(__file__).resolve().parents[1] / "config" / "excluded_students_final_year.csv",
}


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
    def _normalized_last_token(column_name: str) -> str:
        # Flattened headers are joined with underscores, e.g. "Section_USN"
        token = str(column_name).split("_")[-1].strip().upper()
        return token

    # 1) Strong preference: exact USN field (either whole col is USN or ends with _USN)
    usn_col = next(
        (
            col
            for col in df.columns
            if str(col).strip().upper() == "USN" or _normalized_last_token(col) == "USN"
        ),
        None,
    )

    # 2) If not found, prefer any USN column that is NOT the "keep in ascending order" helper
    if usn_col is None:
        usn_col = next(
            (
                col
                for col in df.columns
                if "USN" in str(col).upper()
                and "KEEP DATA IN ASSENDING ORDER" not in str(col).upper()
            ),
            None,
        )

    # 3) Final fallback: first column containing USN
    if usn_col is None:
        usn_col = next((col for col in df.columns if "USN" in str(col).upper()), None)

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
        selected_columns = [email_col, name_col]
        if usn_col is not None:
            selected_columns.append(usn_col)
        selected_columns.extend(score_columns)
        results[skill.name] = {
            "error": None,
            "score_columns": score_columns,
            "data": filtered_df[selected_columns],
        }

    return results


def get_a1_only_filtered_df_for_ui(excel_bytes, sheet_name, semester, column_rename_map):
    """Return students where A1 is below pass and A2 passed.

    For 6th Semester (and when A3 exists), also enforce A3 passed.
    """
    df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=sheet_name, header=[0, 1])
    df = flatten_columns(df)
    df = rename_columns(df, column_rename_map)

    email_col = find_column_by_contains(df, "Email")
    name_col = find_column_by_contains(df, "Name")

    def _normalized_last_token(column_name: str) -> str:
        token = str(column_name).split("_")[-1].strip().upper()
        return token

    usn_col = next(
        (
            col
            for col in df.columns
            if str(col).strip().upper() == "USN" or _normalized_last_token(col) == "USN"
        ),
        None,
    )
    if usn_col is None:
        usn_col = next(
            (
                col
                for col in df.columns
                if "USN" in str(col).upper()
                and "KEEP DATA IN ASSENDING ORDER" not in str(col).upper()
            ),
            None,
        )
    if usn_col is None:
        usn_col = next((col for col in df.columns if "USN" in str(col).upper()), None)

    suffixes = ["A1", "A2"] if semester == "4th Semester" else ["A1", "A2", "A3"]
    score_columns = find_score_columns_by_suffix(df, suffixes)

    for col in score_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    a1_col = next(col for col in score_columns if col.endswith("A1"))
    a2_col = next(col for col in score_columns if col.endswith("A2"))

    mask = (
        (df[a1_col] < PASS_MARKS_REFERENCE["A1"])
        & (df[a2_col] >= PASS_MARKS_REFERENCE["A2"])
    )

    if semester == "6th Semester":
        a3_col = next(col for col in score_columns if col.endswith("A3"))
        mask = mask & (df[a3_col] >= PASS_MARKS_REFERENCE["A3"])

    selected_columns = [email_col, name_col]
    if usn_col is not None:
        selected_columns.append(usn_col)
    selected_columns.extend(score_columns)

    return df.loc[mask, selected_columns], score_columns


def style_below_passing(value, passing_marks):
    try:
        return "color: red; font-weight: 700;" if float(value) < float(passing_marks) else ""
    except (TypeError, ValueError):
        return ""


def round_float_columns(df):
    rounded_df = df.copy()
    float_columns = rounded_df.select_dtypes(include=["floating"]).columns
    if len(float_columns) > 0:
        rounded_df[float_columns] = rounded_df[float_columns].round(1)
    return rounded_df


def center_styler(df):
    return df.style.format(precision=1).set_properties(**{"text-align": "justify", "text-justify": "inter-word"}).set_table_styles(
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


def _join_with_and(items):
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _condition_heading(passed_labels, failed_labels):
    passed_text = _join_with_and(passed_labels)
    failed_text = _join_with_and(failed_labels)

    if passed_text and failed_text:
        return f"{passed_text} passed but {failed_text} failed"
    if failed_text:
        return f"{failed_text} failed"
    return "Filtered Students"


def add_count_row(df, score_columns, passing_marks):
    """Append a count row (below passing marks) to the given table."""
    if df.empty:
        return df

    count_row = {col: "" for col in df.columns}
    label_col = next((col for col in df.columns if col not in score_columns), None)
    if label_col is not None:
        count_row[label_col] = "Red count"

    for col in score_columns:
        numeric_series = pd.to_numeric(df[col], errors="coerce")
        threshold = get_threshold_for_column(col, passing_marks)
        count_row[col] = int((numeric_series < threshold).sum())

    count_df = pd.DataFrame([count_row], index=["Red count"])
    return pd.concat([df, count_df], axis=0)


def normalize_student_name(name):
    return " ".join(str(name).strip().split()).upper()


def load_excluded_students_for_semester(semester):
    file_path = EXCLUDED_STUDENTS_FILES.get(semester)
    if file_path is None:
        return [], None, None

    if not file_path.exists():
        return [], str(file_path), f"Exclude list file not found: {file_path.name}"

    try:
        exclusions_df = pd.read_csv(file_path)
    except Exception as err:
        return [], str(file_path), f"Could not read exclude list: {err}"

    if exclusions_df.empty:
        return [], str(file_path), None

    if "Name" in exclusions_df.columns:
        names_series = exclusions_df["Name"]
    else:
        names_series = exclusions_df.iloc[:, 0]

    seen = set()
    excluded_names = []
    for value in names_series.dropna().astype(str):
        name = value.strip()
        if not name:
            continue
        normalized = normalize_student_name(name)
        if normalized not in seen:
            seen.add(normalized)
            excluded_names.append(name)

    return excluded_names, str(file_path), None


def filter_excluded_students(df, excluded_name_set):
    if df.empty or not excluded_name_set:
        return df, []

    name_col = next((col for col in df.columns if "Name" in str(col)), None)
    if name_col is None:
        return df, []

    normalized_names = df[name_col].astype(str).map(normalize_student_name)
    exclude_mask = normalized_names.isin(excluded_name_set)

    excluded_found = (
        df.loc[exclude_mask, name_col]
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    return df.loc[~exclude_mask].copy(), excluded_found


def render_tyl_analysis_dashboard():
    top_col1, top_col2 = st.columns([1, 6])
    with top_col1:
        if st.button("← Back to Home"):
            st.session_state["current_page"] = "home"
            st.rerun()

    with top_col2:
        st.markdown(
            "<h1 style='text-align: center;'>TYL Analysis Dashboard</h1>",
            unsafe_allow_html=True,
        )
    '''
        Final year tyl eligibility 

        Lx4
        Ax 4
        Cx5
        Px 3.5.or 4
        Sx 3

        6th semester eligibility 
        Lx4
        Ax3
        CX3
        Px3.5 
        Sx 3


        4th semester eligibility 
        Lx 3
        Ax1
        Cx 2
        Px 3
        Sx 2
    '''
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        semester = st.selectbox(
            "Semester",
            options=["4th Semester", "6th Semester", "Final Year"],
        )
    with col2:
        sheets_text = st.text_input("Sheets (comma separated)", "UG-AIML,UG-CSAIML")

    required_below = st.number_input(
            "Subjects scored below passing marks",
            help="e.g. 1 for at least 1 subject, 2 for at least 2 subjects, etc.",
            min_value=1,
            max_value=4,
            value=1,
        )

    st.markdown(
        """
        <style>
        div[data-testid="stButton"] > button[kind="primary"] {
            display: block;
            margin: 0 auto;
            padding: 0.75rem 3rem;
            font-size: 1.2rem;
            font-weight: 700;
            background-color: #1976D2;
            color: white;
            border: none;
            border-radius: 8px;
            white-space: nowrap;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #1565C0;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _, btn_col, _ = st.columns([1, 2, 1])
    if "analysis_in_progress" not in st.session_state:
        st.session_state["analysis_in_progress"] = False

    with btn_col:
        run_clicked = st.button(
            "⏳ Running Analysis..." if st.session_state["analysis_in_progress"] else "🔍 Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=st.session_state["analysis_in_progress"],
        )

    if "analysis_state" not in st.session_state:
        st.session_state["analysis_state"] = None

    if run_clicked:
        st.session_state["analysis_in_progress"] = True
        st.rerun()

    if st.session_state["analysis_in_progress"]:
        semester_skills_map = {
            "4th Semester": {
                "Ax": ["A1", "A2"],
                "Sx": ["S1", "S2"],
            },
            "6th Semester": {
                "Ax": ["A1", "A2", "A3"],
                "Sx": ["S1", "S2", "S3"],
            },
            "Final Year": {
                "Ax": ["A1", "A2", "A3", "A4"],
                "Sx": ["S1", "S2", "S3", "S4"],
            },
        }
        selected_skills = semester_skills_map[semester]
        skills = [
            Skill(
                name=name,
                score_suffixes=suffixes,
                passing_marks={s: PASS_MARKS_REFERENCE.get(s, 50) for s in suffixes},
            )
            for name, suffixes in selected_skills.items()
        ]
        passing_marks_by_skill = {skill.name: skill.passing_marks for skill in skills}

        column_rename_map = {
            "Full Name_As per PAN Card or 10th Mark scard": "Name",
        }

        sheet_names = [s.strip() for s in sheets_text.split(",") if s.strip()]
        excluded_students, excluded_file_path, excluded_error = load_excluded_students_for_semester(semester)

        if uploaded_file is None:
            st.error("Please upload an Excel file.")
            st.session_state["analysis_in_progress"] = False
            return
        excel_bytes = uploaded_file.getvalue()

        with st.spinner("Processing analysis..."):
            results_by_sheet = {}
            a1_only_by_sheet = {}
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

                try:
                    a1_only_df, a1_only_score_columns = get_a1_only_filtered_df_for_ui(
                        excel_bytes,
                        sheet_name,
                        semester,
                        column_rename_map,
                    )
                    a1_only_by_sheet[sheet_name] = {
                        "error": None,
                        "data": a1_only_df,
                        "score_columns": a1_only_score_columns,
                    }
                except Exception as err:
                    a1_only_by_sheet[sheet_name] = {"error": str(err), "data": None, "score_columns": []}

        st.session_state["analysis_state"] = {
            "skills": skills,
            "sheet_names": sheet_names,
            "results_by_sheet": results_by_sheet,
            "passing_marks_by_skill": passing_marks_by_skill,
            "a1_only_by_sheet": a1_only_by_sheet,
            "semester": semester,
            "excluded_students": excluded_students,
            "excluded_file_path": excluded_file_path,
            "excluded_error": excluded_error,
        }
        st.session_state["analysis_in_progress"] = False
        st.rerun()

    analysis_state = st.session_state.get("analysis_state")
    if analysis_state:
        skills = analysis_state["skills"]
        sheet_names = analysis_state["sheet_names"]
        results_by_sheet = analysis_state["results_by_sheet"]
        passing_marks_by_skill = analysis_state["passing_marks_by_skill"]
        a1_only_by_sheet = analysis_state.get("a1_only_by_sheet", {})
        semester = analysis_state.get("semester", "")
        excluded_students = analysis_state.get("excluded_students", [])
        excluded_file_path = analysis_state.get("excluded_file_path")
        excluded_error = analysis_state.get("excluded_error")
        excluded_name_set = {normalize_student_name(name) for name in excluded_students}
        excluded_students_seen_in_output = set()

        if excluded_error:
            st.warning(excluded_error)

        for skill in skills:
            skill_name = skill.name
            st.markdown(f"## Skill {skill_name}")
            combined_frames = []
            score_columns = []
            skill_passing_marks = passing_marks_by_skill.get(skill_name, 50)

            for sheet_name in sheet_names:
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

                current_df = round_float_columns(details["data"]).copy()
                current_df.insert(0, "Sheet", sheet_name)
                combined_frames.append(current_df)
                if not score_columns:
                    score_columns = details["score_columns"]

            if not combined_frames:
                st.info("No matching data available across selected sheets.")
                continue

            filtered_df = pd.concat(combined_frames, ignore_index=True)
            filtered_df, excluded_here = filter_excluded_students(filtered_df, excluded_name_set)
            excluded_students_seen_in_output.update(excluded_here)

            if filtered_df.empty:
                st.info("No matching data available after applying excluded students list.")
                continue

            # Render separate tables with explicit passed/failed condition headings.
            pattern_df = pd.DataFrame(index=filtered_df.index)
            for col in score_columns:
                col_threshold = get_threshold_for_column(col, skill_passing_marks)
                pattern_df[col] = pd.to_numeric(filtered_df[col], errors="coerce") < col_threshold

            grouped_indices = {}
            for row_idx, row in pattern_df.iterrows():
                failed_cols = tuple(col.split("_")[-1] for col in score_columns if bool(row[col]))
                passed_cols = tuple(col.split("_")[-1] for col in score_columns if not bool(row[col]))
                grouped_indices.setdefault((passed_cols, failed_cols), []).append(row_idx)

            if not grouped_indices:
                st.markdown(f"#### {semester} - Filtered Students")

            for (passed_cols, failed_cols), row_indices in grouped_indices.items():
                heading = _condition_heading(list(passed_cols), list(failed_cols))
                st.markdown(f"#### {semester} - {heading}")
                sub_df = filtered_df.loc[row_indices]
                st.write(f"Students matched: {len(sub_df)}")
                sub_df_with_count = add_count_row(sub_df, score_columns, skill_passing_marks)
                styled_sub_df = sub_df_with_count.style
                data_row_indices = [idx for idx in sub_df_with_count.index if idx != "Red count"]
                for col in score_columns:
                    col_threshold = get_threshold_for_column(col, skill_passing_marks)
                    styled_sub_df = styled_sub_df.map(
                        lambda value, t=col_threshold: style_below_passing(value, t),
                        subset=pd.IndexSlice[data_row_indices, [col]],
                    )
                styled_sub_df = styled_sub_df.format(precision=1).set_properties(**{"text-align": "justify", "text-justify": "inter-word"}).set_table_styles(
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
                st.dataframe(styled_sub_df, use_container_width=True)

            if skill_name == "Ax":
                if semester == "6th Semester":
                    st.caption("Condition: A1 < pass, A2 ≥ pass, and A3 ≥ pass")
                else:
                    st.caption("Condition: A1 < pass and A2 ≥ pass")

                merged_special_frames = []
                special_score_columns = []
                for sheet_name in sheet_names:
                    special = a1_only_by_sheet.get(sheet_name, {})

                    if special.get("error"):
                        st.warning(f"Could not build A1 special table for {sheet_name}: {special['error']}")
                        continue

                    special_df = special.get("data")
                    if special_df is None:
                        continue

                    special_df = round_float_columns(special_df).copy()
                    special_df.insert(0, "Sheet", sheet_name)
                    merged_special_frames.append(special_df)
                    if not special_score_columns:
                        special_score_columns = special.get("score_columns", [])

                if merged_special_frames:
                    special_df = pd.concat(merged_special_frames, ignore_index=True)
                    special_df, excluded_here = filter_excluded_students(special_df, excluded_name_set)
                    excluded_students_seen_in_output.update(excluded_here)

                    if special_df.empty:
                        st.info("No Ax special-case students after applying excluded students list.")
                        continue

                    if semester == "6th Semester":
                        st.markdown(f"#### {semester} - A2 and A3 passed but A1 failed")
                    else:
                        st.markdown(f"#### {semester} - A2 passed but A1 failed")
                    st.write(f"Students matched: {len(special_df)}")

                    styled_special_df_with_count = add_count_row(
                        special_df,
                        special_score_columns,
                        {"A1": PASS_MARKS_REFERENCE["A1"], "A2": PASS_MARKS_REFERENCE["A2"], "A3": PASS_MARKS_REFERENCE["A3"]},
                    )
                    styled_special_df = styled_special_df_with_count.style
                    special_data_row_indices = [idx for idx in styled_special_df_with_count.index if idx != "Red count"]
                    for col in special_score_columns:
                        col_threshold = get_threshold_for_column(col, {"A1": PASS_MARKS_REFERENCE["A1"], "A2": PASS_MARKS_REFERENCE["A2"], "A3": PASS_MARKS_REFERENCE["A3"]})
                        styled_special_df = styled_special_df.map(
                            lambda value, t=col_threshold: style_below_passing(value, t),
                            subset=pd.IndexSlice[special_data_row_indices, [col]],
                        )
                    styled_special_df = styled_special_df.format(precision=1).set_properties(**{"text-align": "justify", "text-justify": "inter-word"}).set_table_styles(
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
                    st.dataframe(styled_special_df, use_container_width=True)

        st.markdown("## Excluded Students")
        if excluded_file_path:
            st.caption(f"Source file: {excluded_file_path}")

        if excluded_students:
            excluded_seen_normalized = {normalize_student_name(name) for name in excluded_students_seen_in_output}
            excluded_df = pd.DataFrame(
                {
                    "Name": excluded_students,
                    "Found in uploaded data": [
                        "Yes" if normalize_student_name(name) in excluded_seen_normalized else "No"
                        for name in excluded_students
                    ],
                }
            )
            st.table(center_styler(excluded_df))
        else:
            st.info("No excluded students configured for this semester.")

    st.divider()
    with st.container(border=True):
        st.markdown(
            "<p style='color: grey; font-style: italic;'>📋 The following tables are for reference only.</p>",
            unsafe_allow_html=True,
        )
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
