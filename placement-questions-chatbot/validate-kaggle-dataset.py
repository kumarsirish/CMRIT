# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
import kagglehub
from kagglehub import KaggleDatasetAdapter

# Kaggle dataset handle and file name inside the uploaded dataset.
DATASET_HANDLE = "sirishk99/cmrti-placement-questions-dataset"
FILE_PATH = "undergrad-cs-questions-data.parquet"


if not FILE_PATH:
    raise ValueError("Set FILE_PATH to a supported file in the Kaggle dataset, such as a .parquet file.")

# Load the latest version
df = kagglehub.load_dataset(
  KaggleDatasetAdapter.PANDAS,
  DATASET_HANDLE,
  FILE_PATH,
  # Provide any additional arguments like 
  # sql_query or pandas_kwargs. See the 
  # documenation for more information:
  # https://github.com/Kaggle/kagglehub/blob/main/README.md#kaggledatasetadapterpandas
)

print("First 5 records:", df.head())
# print text field for the source 'pdf'
pdf_texts = df[df['source_type'] == 'pdf']['text']
print("First 5 PDF texts:", pdf_texts.head())