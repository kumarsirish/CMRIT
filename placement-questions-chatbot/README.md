## Files
### Step 1
**Create the questions-data**
Download all the excel and pdfs at one place inside the questions-data directory
### Step 2 - Initial Preprocessing
**preprocess-excel-files.py**
This files takes all the excel files and coverts them into the csv files. It also drops s.no and personal interaction columns and renames the columns
### Step 3 - Create and upload the Parquet file to  Kaggle
**create-parquet-package.py**: This file creates Parquet package inside the dataset directory
**upload-parquet-kaggle.sh**:Upload the dataset to Kaggle
**validate-kaggle-dataset.py**: download and verify the kaggle dataset

