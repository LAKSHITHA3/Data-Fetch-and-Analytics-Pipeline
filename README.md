# Data-Fetch-and-Analytics-Pipeline

Climate Data Processing Pipeline with Apache Airflow and Apache Beam
This repository implements a data engineering pipeline for acquiring and processing climatological data from the National Centers for Environmental Information (NCEI).

Data Acquisition Pipeline (Pipeline 1):

Fetches the webpage containing location-wise datasets for a specific year using a Bash Operator with wget or curl.
Selects a random subset of data files using a Python Operator.
Downloads the selected individual data files using a Bash or Python Operator.
Zips the downloaded files into an archive using a Python Operator.
Places the archive at a designated location using a Bash or Python Operator.

Data Processing Pipeline (Pipeline 2):

Uses a FileSensor to wait for the archive to become available at the designated location (with a timeout).
Unzips the archive and extracts individual CSV files using a Bash Operator.
Processes each CSV file in parallel using Apache Beam with DirectRunner:
Extracts data into a Pandas DataFrame.
Filters the DataFrame for specific fields (e.g., windspeed, temperature) and retrieves latitude/longitude values.
Computes monthly averages of the required fields.
Creates visualizations (heatmaps) using geopandas and geodatasets libraries. Exports plots as PNG images.
(Optional) Creates a GIF animation using ffmpeg or equivalent tool from the PNG images.
Deletes the processed CSV files.

Key Technologies:

Apache Airflow for workflow orchestration.
Apache Beam for parallel data processing.
Python for data manipulation and visualization.
Bash for system commands.

Note:

This repository requires separate Python files for DAGs and Beam pipelines.
The code prioritizes clean coding style, correctness, readability, and input validation.


Getting Started:

Clone this repository.

Install required dependencies (refer to code for details).

Configure Airflow connection details and DAG parameters.

Run Airflow to execute the pipelines.
