from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import random
import os
import shutil
import zipfile
import logging
import requests
from bs4 import BeautifulSoup

# Define base URL
BASE_URL = "https://www.ncei.noaa.gov/data/local-climatological-data/access/"

# Function to fetch the page containing location wise datasets
def fetch_page(year):
    """
    Fetches the page containing location-wise datasets for a given year.
    """
    try:
        if not (1901 <= year <= 2024):
            raise ValueError("Year must be between 1901 and 2024.")
        
        command = f"curl {BASE_URL}/{year}/ -o {year}_data.html"
        os.system(command)
        logging.info(f"Page fetched for year {year}.")
    except Exception as e:
        logging.error(f"Error fetching page for year {year}: {str(e)}")

def get_available_files(url):
    """
    Fetches the list of available files from the given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        file_links = [link['href'] for link in soup.find_all('a') if link['href'].endswith('.csv')]
        
        return file_links
    except Exception as e:
        logging.error(f"Error fetching available files from {url}: {str(e)}")
        return []

# Function to select random data files
def select_files(year, num_files):
    """
    Selects random data files from a list of available files.
    """
    try:
        if not 1901 <= year <= 2024:
            raise ValueError("Year must be between 1901 and 2024.")
        if not isinstance(num_files, int) or num_files <= 0:
            raise ValueError("Number of files must be a positive integer.")

        url = f"{BASE_URL}/{year}/"
        available_files = get_available_files(url)
        selected_files = random.sample(available_files, min(num_files, len(available_files)))
        
        logging.info(f"Selected files for year {year}: {selected_files}")
        return selected_files
    except Exception as e:
        logging.error(f"Error selecting files for year {year}: {str(e)}")

# Function to fetch individual data files
def fetch_data_file(year, file_name, output_dir):
    """
    Fetches an individual data file.
    """
    try:
        if not (1901 <= year <= 2024):
            raise ValueError("Year must be between 1901 and 2024.")
        if not os.path.exists(output_dir):
            raise ValueError("Output directory does not exist.")

        file_url = f"{BASE_URL}/{year}/{file_name}"
        command = f"curl {file_url} -o {output_dir}/{file_name}"
        os.system(command)

        logging.info(f"Data file {file_name} fetched for year {year}.")
    except Exception as e:
        logging.error(f"Error fetching data file {file_name} for year {year}: {str(e)}")

# Function to zip data files into an archive
def zip_files(files, output_dir, output_filename):
    """
    Zips data files into an archive.
    """
    try:
        if not os.path.exists(output_dir):
            raise ValueError("Output directory does not exist.")
        if not files:
            raise ValueError("Files list is empty.")

        output_path = os.path.join(output_dir, output_filename)
        with zipfile.ZipFile(output_path, 'w') as zipf:
            for file in files:
                file_path = os.path.join(output_dir, file)
                zipf.write(file_path, arcname=file)
        
        logging.info(f"Archive {output_filename} created successfully.")
    except Exception as e:
        logging.error(f"Error creating archive {output_filename}: {str(e)}")

# Function to place the archive at a required location
def move_archive(archive, destination):
    """
    Moves the archive to the specified destination.
    """
    try:
        if not os.path.exists(destination):
            raise ValueError("Destination directory does not exist.")
        if not os.path.exists(archive):
            raise ValueError("Archive file does not exist.")

        shutil.move(archive, destination)
        logging.info(f"Archive moved to {destination}.")
    except Exception as e:
        logging.error(f"Error moving archive to {destination}: {str(e)}")

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 2),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1
}

# Define variables
year = '2022'  # Replace 'YYYY' with the actual year value
num_files = 6  # Specify the number of files

# Create the DAG object
with DAG('data_fetch_pipeline', default_args=default_args, schedule=None) as dag:
    
    fetch_page_task = PythonOperator(
        task_id='fetch_page',
        python_callable=fetch_page,
        op_kwargs={'year': year}  
    )

    select_files_task = PythonOperator(
        task_id='select_files',
        python_callable=select_files,
        op_kwargs={'year': year, 'num_files': num_files}  
    )

    fetch_data_files = [PythonOperator(
        task_id=f'fetch_data_file_{i}',
        python_callable=fetch_data_file,
        op_kwargs={'year': year, 'file_name': file, 'output_dir': '/tmp'}  # Year and output_dir can be parameterized
    ) for i, file in enumerate(range(num_files))]  

    zip_files_task = PythonOperator(
        task_id='zip_files',
        python_callable=zip_files,
        op_kwargs={'files': [f'file{i}.txt' for i in range(1, num_files+1)], 'output_dir': '/tmp/', 'output_filename': 'archive.zip'} 
    )

    move_archive_task = PythonOperator(
        task_id='move_archive',
        python_callable=move_archive,
        op_kwargs={'archive': '/home/lucky/Data-Fetch-and-Analytics-Pipeline/archive.zip', 'destination': r'//wsl.localhost/Ubuntu/home/lucky/Assign2'}  
    )

    fetch_page_task >> select_files_task >> fetch_data_files >> zip_files_task >> move_archive_task
