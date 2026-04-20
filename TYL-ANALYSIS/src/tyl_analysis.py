import pandas as pd
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Skill:
    name: str
    score_suffixes: List[str]
    passing_marks: int

    def score_suffix_patterns(self):
        return self.score_suffixes


def flatten_columns(df):
    new_columns = []
    for col in df.columns:
        parts = []
        for c in col:
            if pd.notna(c):
                parts.append(str(c).strip())
        new_columns.append("_".join(parts))
    df.columns = new_columns
    return df


def rename_columns(df, column_rename_map: Dict[str, str]):
    if column_rename_map:
        df = df.rename(columns=column_rename_map)
    return df


def find_column_by_contains(df, text):
    for col in df.columns:
        if text in col:
            return col
    raise ValueError(f"Column containing '{text}' not found")


def find_score_columns_by_suffix(df, suffix_patterns):
    score_columns = []
    for suffix in suffix_patterns:
        matched = None
        for col in df.columns:
            if col.endswith(suffix):
                matched = col
                break
        if matched is None:
            raise ValueError(f"Column ending with '{suffix}' not found")
        score_columns.append(matched)
    return score_columns


def get_filtered_df(df, score_columns, passing_marks, required_below_count):
    for col in score_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    condition = (df[score_columns] < passing_marks).sum(axis=1) == required_below_count
    return df[condition]


def process_sheet(
    file_path,
    sheet_name,
    skills,
    required_columns_below_passing_marks,
    column_rename_map,
):
    print(f"\n===== Processing sheet: {sheet_name} =====")

    # --- READ EXCEL WITH MULTI-LEVEL HEADER ---
    # First two rows are headers, so we use header=[0,1] to read them as a MultiIndex
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=[0, 1])

    # --- FLATTEN COLUMNS ---
    df = flatten_columns(df)

    # --- RENAME COLUMNS (optional) ---
    df = rename_columns(df, column_rename_map)

    email_col = find_column_by_contains(df, "Email")
    name_col = find_column_by_contains(df, "Name")

    for skill in skills:
        # --- IDENTIFY REQUIRED COLUMNS ---
        try:
            score_columns = find_score_columns_by_suffix(df, skill.score_suffix_patterns())
        except ValueError as err:
            print(f"Skipping skill {skill.name} in {sheet_name}: {err}")
            continue

        print(f"Identified score columns for {skill.name}: {score_columns}")

        # --- FILTER STUDENTS ---
        filtered_df = get_filtered_df(
            df,
            score_columns,
            skill.passing_marks,
            required_columns_below_passing_marks,
        )

        print(
            f"Number of students with exactly {required_columns_below_passing_marks} score(s) < {skill.passing_marks} for {skill.name}: {len(filtered_df)}"
        )
        print("Filtered students:")
        print(filtered_df[[email_col, name_col, *score_columns]])

        for col in score_columns:
            condition = filtered_df[col] < skill.passing_marks
            filtered_df1 = filtered_df[condition]
            print(
                f"Number of students with exactly {required_columns_below_passing_marks} score(s) < {skill.passing_marks} in {col}: {len(filtered_df1)}"
            )
            print(f"Filtered students for {col}:")
            print(filtered_df1[[email_col, name_col, col]])


def main(file_path=None):
    # --- CONFIG ---
    if file_path is None:
        file_path = input("Enter Excel file path (default: TYL.xlsx): ").strip()

    sheet_names = ["UG-AIML", "UG-CSAIML"]
    skills = [
        Skill(name="A", score_suffixes=["A1", "A2", "A3"], passing_marks=50),
        Skill(name="S", score_suffixes=["S1", "S2", "S3"], passing_marks=50),
    ]
    required_columns_below_passing_marks = 1
    column_rename_map = {
        # Example:
        # "Student_Email Address": "Email",
        "Full Name_As per PAN Card or 10th Mark scard": "Name",
    }

    for sheet_name in sheet_names:
        process_sheet(
            file_path,
            sheet_name,
            skills,
            required_columns_below_passing_marks,
            column_rename_map,
        )


if __name__ == "__main__":
    main()