#read and parse excel files
import pandas as pd
import os
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_file_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        with open(pdf_file_path, "rb") as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF {pdf_file_path}: {e}")
    return text


def detect_header_row(exfile, keyword="technical questions", scan_rows=30):
    preview_df = pd.read_excel(exfile, header=None, nrows=scan_rows)

    for row_index, row in preview_df.iterrows():
        row_text = " ".join(row.fillna("").astype(str).tolist()).strip().casefold()
        if keyword.casefold() in row_text:
            return row_index

    return 0


def process_excel_file(exfile):
    header_row = detect_header_row(exfile, keyword="technical questions")
    df = pd.read_excel(exfile, header=header_row)
    df.columns = [str(col).strip() for col in df.columns]
    # Display the first few rows of the DataFrame
    #print(df.head())
       #print(df.head())
    # remove S.No and Personal Interaction columns (ignore case + spaces)
    normalized_column_map = {str(col).strip().casefold(): col for col in df.columns}
    columns_to_drop = []

    #s.no or sno or serial no
    # drop first coumn assuming it contains s.no
    first_col = df.columns[0]
    df = df.drop(columns=[first_col])

    # if second column contains 'name' or 'company' then rename it to 'company name'
    second_col = df.columns[0]
    second_col_text = str(second_col).strip().casefold()
    if "name" in second_col_text or "company" in second_col_text:
        df = df.rename(columns={second_col: "company name"})
    
    #remove 'Personal Interaction' column if it exists
    for col_name in normalized_column_map:
        if "personal interaction".casefold() in col_name:
            columns_to_drop.append(normalized_column_map[col_name])

    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
    print("Columns after dropping:", df.columns)
    print("Number of rows after dropping:", len(df))
    return df

    
if __name__ == "__main__":
    # Path to the Excel file
    
    # list all supported files recursively and process each file
    directory = "/home/sirkumar/CMRIT-AIML/placement-questions-chatbot/questions-data/"
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            lower_name = filename.casefold()

            if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
                print(f"Processing file: {file_path}")
                df = process_excel_file(file_path)
                csv_file_path = os.path.splitext(file_path)[0] + ".csv"
                df.to_csv(csv_file_path, index=False)
                print(f"Saved processed data to: {csv_file_path}")

            