# Read PDF and CSV files from questions-data directory and create parquet file for kaggle dataset
import os
import pandas as pd
import PyPDF2


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text() or ""
            text += page_text
    return text


def extract_text_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    return df.fillna("").to_string(index=False)


def iter_supported_files(input_directory):
    for root, _, files in os.walk(input_directory):
        for filename in files:
            lower_name = filename.lower()
            if lower_name.endswith('.pdf') or lower_name.endswith('.csv'):
                file_path = os.path.join(root, filename)
                yield file_path


def create_parquet_from_documents(input_directory, output_parquet):
    data = []
    for file_path in iter_supported_files(input_directory):
        filename = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, input_directory)
        file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
            source_type = 'pdf'
        elif filename.lower().endswith('.csv'):
            text = extract_text_from_csv(file_path)
            source_type = 'csv'
        else:
            continue

        data.append(
            {
                'filename': filename,
                'relative_path': relative_path,
                'source_type': source_type,
                'file_size_kb': file_size_kb,
                'text': text,
                'text_length': len(text)
            }
        )

    df = pd.DataFrame(data)
    df.to_parquet(output_parquet, index=False)

    summary_columns = ['filename', 'relative_path', 'source_type', 'file_size_kb', 'text_length']
    summary_df = df[summary_columns]

    print("\nFile summary:")
    if summary_df.empty:
        print("No supported files found.")
    else:
        print(summary_df.to_string(index=False))

    return summary_df


if __name__ == "__main__":
    input_directory = './questions-data'
    output_parquet = 'dataset/undergrad-cs-questions-data.parquet'
    create_parquet_from_documents(input_directory, output_parquet)