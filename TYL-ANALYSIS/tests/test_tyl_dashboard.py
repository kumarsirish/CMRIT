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
