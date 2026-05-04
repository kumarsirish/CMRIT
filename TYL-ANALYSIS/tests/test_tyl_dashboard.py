from pathlib import Path

import pandas as pd
import pytest

from tyl_analysis import Skill
from tyl_dashboard import process_sheet_for_ui


PASSING_MARKS = 50
REQUIRED_BELOW_COUNT = 1
SHEET_NAME = "UG-AIML"

# Fill this with your expected student names for:
# A2 < 50 and A1 >= 50 and A3 >= 50 in UG-AIML.
EXPECTED_UG_AIML_A2_ONLY_NAMES = [
    "Ankitha N",
    "Bar shaik Aarzoo Nuha",
    "DILEEP M N",
    "MOHNISH JAKHAR",
    "NIHA MUSKAAN SHARIEF",
    "PALAKONDA SAI KIRAN",
    "SAMIKSHA S SHETTY",
    "SHIVAM ARYA",
    "SHOMITH R",
    "Shreyas Hemmady",
    "Srishti Sangayya Malimath",
    "Tannushree Vaishnav",
    "THEJASHWINI R",
    "Vinay Kumar H R",
    "Yashaswini N",
    "Yashica G",
    "SYED ANSHU"
]

# Sx3 < 50 in UG-AIML.
EXPECTED_UG_AIML_Sx3_ONLY_NAMES = [
    "Bishal Chaudhary",
    "Kirtan Shrestha",
    "GAGAN.K",
    "NICHENAMETLA PRANATHI",
    "Priyanshu Lohani",
    "R SUDHIRKUMAR",
    "Rachit Garg",
    "RAKSHITHA PATIL S",
    "RAMAKRISHNAN VINUSH",
    "SAI HARSHA K",
    "SANJANNA RAMESHH",
    "Tanish Tammanna Pandiyanda",
    "Muhammad Ahmad",
    "SHIVAM ARYA",
    "Yashaswini N",
    
]

EXPECTED_UG_AIML_Sx1_ONLY_NAMES: list[str] = [
    "ANANYA YAMBA",
    "Vikram S",
]


def _get_excel_bytes() -> bytes:
    excel_path = Path(__file__).resolve().parents[1] / "tests" / "TYL-TEST.xlsx"
    if not excel_path.exists():
        pytest.skip("TYL.xlsx not found in project root")
    return excel_path.read_bytes()


def _get_ax_dataframe_for_sheet(sheet_name: str) -> pd.DataFrame:
    excel_bytes = _get_excel_bytes()

    skills = [
        Skill(name="Ax", score_suffixes=["A1", "A2", "A3"], passing_marks=PASSING_MARKS),
        Skill(name="Sx", score_suffixes=["S1", "S2", "S3"], passing_marks=PASSING_MARKS),
    ]

    column_rename_map = {
        "Full Name_As per PAN Card or 10th Mark scard": "Name",
    }

    result = process_sheet_for_ui(
        excel_bytes=excel_bytes,
        sheet_name=sheet_name,
        skills=skills,
        required_columns_below_passing_marks=REQUIRED_BELOW_COUNT,
        column_rename_map=column_rename_map,
    )

    ax_details = result.get("Ax")
    assert ax_details is not None, "Ax result is missing"
    assert ax_details["error"] is None, f"Ax processing error: {ax_details['error']}"

    return ax_details["data"]


def _get_sx_dataframe_for_sheet(sheet_name: str) -> pd.DataFrame:
    excel_bytes = _get_excel_bytes()

    skills = [
        Skill(name="Ax", score_suffixes=["A1", "A2", "A3"], passing_marks=PASSING_MARKS),
        Skill(name="Sx", score_suffixes=["S1", "S2", "S3"], passing_marks=PASSING_MARKS),
    ]

    column_rename_map = {
        "Full Name_As per PAN Card or 10th Mark scard": "Name",
    }

    result = process_sheet_for_ui(
        excel_bytes=excel_bytes,
        sheet_name=sheet_name,
        skills=skills,
        required_columns_below_passing_marks=REQUIRED_BELOW_COUNT,
        column_rename_map=column_rename_map,
    )

    sx_details = result.get("Sx")
    assert sx_details is not None, "Sx result is missing"
    assert sx_details["error"] is None, f"Sx processing error: {sx_details['error']}"

    return sx_details["data"]


def test_process_sheet_for_ui_returns_ax_data_for_ug_aiml():
    ax_df = _get_ax_dataframe_for_sheet(SHEET_NAME)

    assert not ax_df.empty, "Ax filtered data is empty for UG-AIML"
    assert any(col.endswith("A1") for col in ax_df.columns)
    assert any(col.endswith("A2") for col in ax_df.columns)
    assert any(col.endswith("A3") for col in ax_df.columns)


def test_ug_aiml_a2_only_names_match_expected():
    if not EXPECTED_UG_AIML_A2_ONLY_NAMES:
        pytest.skip("Add expected names to EXPECTED_UG_AIML_A2_ONLY_NAMES before running this test")

    ax_df = _get_ax_dataframe_for_sheet(SHEET_NAME)

    a1_col = next(col for col in ax_df.columns if col.endswith("A1"))
    a2_col = next(col for col in ax_df.columns if col.endswith("A2"))
    a3_col = next(col for col in ax_df.columns if col.endswith("A3"))
    name_col = next(col for col in ax_df.columns if "Name" in col)

    a1_series = pd.to_numeric(ax_df[a1_col], errors="coerce")
    a2_series = pd.to_numeric(ax_df[a2_col], errors="coerce")
    a3_series = pd.to_numeric(ax_df[a3_col], errors="coerce")

    mask = (a2_series < PASSING_MARKS) & (a1_series >= PASSING_MARKS) & (a3_series >= PASSING_MARKS)

    actual_names = (
        ax_df.loc[mask, name_col]
        .astype(str)
        .str.strip()
        .tolist()
    )

    assert sorted(actual_names) == sorted(EXPECTED_UG_AIML_A2_ONLY_NAMES)


# ---------------------------------------------------------------------------
# Sx S3-only tests – UG-AIML
# ---------------------------------------------------------------------------

def _get_ug_aiml_s3_only_names() -> list[str]:
    """Return names of students who passed S1 & S2 but failed S3."""
    import io
    from tyl_analysis import flatten_columns, rename_columns, find_column_by_contains, find_score_columns_by_suffix

    excel_bytes = _get_excel_bytes()
    column_rename_map = {"Full Name_As per PAN Card or 10th Mark scard": "Name"}

    df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=SHEET_NAME, header=[0, 1])
    df = flatten_columns(df)
    df = rename_columns(df, column_rename_map)

    s1_col = find_score_columns_by_suffix(df, ["S1"])[0]
    s2_col = find_score_columns_by_suffix(df, ["S2"])[0]
    s3_col = find_score_columns_by_suffix(df, ["S3"])[0]
    name_col = find_column_by_contains(df, "Name")

    df[s1_col] = pd.to_numeric(df[s1_col], errors="coerce").fillna(0)
    df[s2_col] = pd.to_numeric(df[s2_col], errors="coerce").fillna(0)
    df[s3_col] = pd.to_numeric(df[s3_col], errors="coerce").fillna(0)
    filtered = df[(df[s1_col] >= PASSING_MARKS) & (df[s2_col] >= PASSING_MARKS) & (df[s3_col] < PASSING_MARKS)]

    return filtered[name_col].astype(str).str.strip().tolist()


def test_ug_aiml_sx3_only_names_match_expected():
    """Positive: students who passed S1 & S2 but failed S3 must exactly match the expected list."""
    actual_names = _get_ug_aiml_s3_only_names()
    #print(f"Actual S3-only names: {sorted(actual_names)}")
    #print(f"Expected S3-only names: {sorted(EXPECTED_UG_AIML_Sx3_ONLY_NAMES)}")
    assert sorted(actual_names) == sorted(EXPECTED_UG_AIML_Sx3_ONLY_NAMES), (
        f"Mismatch.\n  Extra  : {sorted(set(actual_names) - set(EXPECTED_UG_AIML_Sx3_ONLY_NAMES))}\n"
        f"  Missing: {sorted(set(EXPECTED_UG_AIML_Sx3_ONLY_NAMES) - set(actual_names))}"
    )


def test_ug_aiml_sx3_only_excludes_passing_students():
    """Negative: no student in the expected list should have S1 or S2 < passing marks."""
    import io
    from tyl_analysis import flatten_columns, rename_columns, find_column_by_contains, find_score_columns_by_suffix

    excel_bytes = _get_excel_bytes()
    column_rename_map = {"Full Name_As per PAN Card or 10th Mark scard": "Name"}

    df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=SHEET_NAME, header=[0, 1])
    df = flatten_columns(df)
    df = rename_columns(df, column_rename_map)

    s1_col = find_score_columns_by_suffix(df, ["S1"])[0]
    s2_col = find_score_columns_by_suffix(df, ["S2"])[0]
    name_col = find_column_by_contains(df, "Name")

    df[s1_col] = pd.to_numeric(df[s1_col], errors="coerce").fillna(0)
    df[s2_col] = pd.to_numeric(df[s2_col], errors="coerce").fillna(0)

    # Students who failed S1 or S2 — none of these should be in the expected list
    failed_s1_or_s2 = df.loc[(df[s1_col] < PASSING_MARKS) | (df[s2_col] < PASSING_MARKS), name_col].astype(str).str.strip().tolist()

    overlap = set(failed_s1_or_s2) & set(EXPECTED_UG_AIML_Sx3_ONLY_NAMES)
    assert not overlap, (
        f"These students failed S1 or S2 but appear in the S3-only expected list: {sorted(overlap)}"
    )


# ---------------------------------------------------------------------------
# Sx S1-only tests – UG-AIML
# ---------------------------------------------------------------------------

def _get_ug_aiml_s1_only_names() -> list[str]:
    """Return names of students who failed S1 but passed S2 & S3."""
    import io
    from tyl_analysis import flatten_columns, rename_columns, find_column_by_contains, find_score_columns_by_suffix

    excel_bytes = _get_excel_bytes()
    column_rename_map = {"Full Name_As per PAN Card or 10th Mark scard": "Name"}

    df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=SHEET_NAME, header=[0, 1])
    df = flatten_columns(df)
    df = rename_columns(df, column_rename_map)

    s1_col = find_score_columns_by_suffix(df, ["S1"])[0]
    s2_col = find_score_columns_by_suffix(df, ["S2"])[0]
    s3_col = find_score_columns_by_suffix(df, ["S3"])[0]
    name_col = find_column_by_contains(df, "Name")

    df[s1_col] = pd.to_numeric(df[s1_col], errors="coerce").fillna(0)
    df[s2_col] = pd.to_numeric(df[s2_col], errors="coerce").fillna(0)
    df[s3_col] = pd.to_numeric(df[s3_col], errors="coerce").fillna(0)
    filtered = df[
        (df[s1_col] < PASSING_MARKS)
        & (df[s2_col] >= PASSING_MARKS)
        & (df[s3_col] >= PASSING_MARKS)
    ]

    return filtered[name_col].astype(str).str.strip().tolist()


def test_ug_aiml_sx1_only_names_match_expected():
    """Positive: students who failed S1 but passed S2 & S3 must exactly match the expected list."""
    if not EXPECTED_UG_AIML_Sx1_ONLY_NAMES:
        pytest.skip("Add expected names to EXPECTED_UG_AIML_Sx1_ONLY_NAMES before running this test")

    actual_names = _get_ug_aiml_s1_only_names()
    assert sorted(actual_names) == sorted(EXPECTED_UG_AIML_Sx1_ONLY_NAMES), (
        f"Mismatch.\n  Extra  : {sorted(set(actual_names) - set(EXPECTED_UG_AIML_Sx1_ONLY_NAMES))}\n"
        f"  Missing: {sorted(set(EXPECTED_UG_AIML_Sx1_ONLY_NAMES) - set(actual_names))}"
    )


def test_ug_aiml_sx1_only_excludes_failing_s2_or_s3_students():
    """Negative: no student in the expected list should have S2 or S3 < passing marks."""
    import io
    from tyl_analysis import flatten_columns, rename_columns, find_column_by_contains, find_score_columns_by_suffix

    excel_bytes = _get_excel_bytes()
    column_rename_map = {"Full Name_As per PAN Card or 10th Mark scard": "Name"}

    df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=SHEET_NAME, header=[0, 1])
    df = flatten_columns(df)
    df = rename_columns(df, column_rename_map)

    s1_col = find_score_columns_by_suffix(df, ["S1"])[0]
    s2_col = find_score_columns_by_suffix(df, ["S2"])[0]
    s3_col = find_score_columns_by_suffix(df, ["S3"])[0]
    name_col = find_column_by_contains(df, "Name")

    df[s1_col] = pd.to_numeric(df[s1_col], errors="coerce").fillna(0)
    df[s2_col] = pd.to_numeric(df[s2_col], errors="coerce").fillna(0)
    df[s3_col] = pd.to_numeric(df[s3_col], errors="coerce").fillna(0)

    # Students who failed S2 or S3 — none of these should be in the expected list
    failed_s2_or_s3 = df.loc[
        (df[s2_col] < PASSING_MARKS) | (df[s3_col] < PASSING_MARKS),
        name_col,
    ].astype(str).str.strip().tolist()

    overlap = set(failed_s2_or_s3) & set(EXPECTED_UG_AIML_Sx1_ONLY_NAMES)
    assert not overlap, (
        f"These students failed S2 or S3 but appear in the S1-only expected list: {sorted(overlap)}"
    )
