from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from datetime import datetime, timedelta
import os
import pandas as pd
import apache_beam as beam
import logging
import zipfile

# Define the DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 2),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Define the DAG object
with DAG('analytics_pipeline', default_args=default_args, schedule=None) as dag:

    # Function to check if archive is valid
    def check_archive(archive_path):
        if not os.path.exists(archive_path):
            return "archive_missing"
        elif not zipfile.is_zipfile(archive_path):
            return "invalid_archive"
        else:
            return "valid_archive"

    # Function to unzip archive
    def unzip_archive(archive_path, extract_path):
        try:
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        except Exception as e:
            logging.error(f"Error unzipping archive: {e}")
            raise

    # Function to delete CSV file
    def delete_csv(csv_path):
        try:
            os.remove(csv_path)
        except Exception as e:
            logging.error(f"Error deleting CSV file: {e}")
            raise

    # Function to process CSV files with Apache Beam
    def process_csv(csv_path):
        try:
            with beam.Pipeline() as pipeline:
                (pipeline | 'Read CSV' >> beam.io.ReadFromText(csv_path)
                          | 'Filter Data' >> beam.ParDo(FilterData())
                          | 'Calculate Monthly Averages' >> beam.ParDo(CalculateMonthlyAverages())
                          | 'Create Heatmap Visualization' >> beam.ParDo(CreateHeatmapVisualization()))
        except Exception as e:
            logging.error(f"Error processing CSV: {e}")
            raise

    # File sensor to wait for archive availability
    wait_for_archive = FileSensor(
        task_id='wait_for_archive',
        filepath='/home/lucky/Assign2/archive.zip',
        timeout=5,
        poke_interval=1,
        mode='poke'
    )

    # Branch operator based on archive status
    check_archive_task = BranchPythonOperator(
        task_id='check_archive',
        python_callable=check_archive,
        op_kwargs={'archive_path': '/home/lucky/Assign2/archive.zip'}
    )

    # Tasks for handling different scenarios
    unzip_task = BashOperator(
        task_id='unzip_archive',
        bash_command='unzip /home/lucky/Assign2/archive.zip -d /home/lucky/Assign2/extracted_files',
        retries=1,
        retry_delay=timedelta(seconds=30)
    )

    delete_csv_task = PythonOperator(
        task_id='delete_csv',
        python_callable=delete_csv,
        op_kwargs={'csv_path': '/home/lucky/Assign2/extracted_files/data.csv'}
    )

    process_csv_task = PythonOperator(
        task_id='process_csv',
        python_callable=process_csv,
        op_kwargs={'csv_path': '/home/lucky/Assign2/extracted_files/data.csv'}
    )
    from airflow.operators.bash_operator import BashOperator

    # Task to create GIF animation using PNG images
    create_gif_task = BashOperator(
    task_id='create_gif_animation',
    bash_command='ffmpeg -framerate 1 -pattern_type glob -i "/path/to/png_images/*.png" -vf "fps=25,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" /path/to/output.gif',
    retries=1,
    retry_delay=timedelta(seconds=30)
)
    # Task dependencies
    wait_for_archive >> check_archive_task
    check_archive_task >> unzip_task >> delete_csv_task >> process_csv_task
    process_csv_task >> create_gif_task
