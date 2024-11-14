# Results Scraper Flask App

This is a Flask web application designed to scrape student results from a specified results portal. The app allows users to input the result link, college code, field code, and year to fetch results and display them in a tabular format. Additionally, users can download the results as an Excel sheet.

## Features

- Scrape and display student results in a tabular format
- Download the results table as an Excel sheet.

## Prerequisites

Make sure you have the following installed:

- Python 3.x
- Flask
- Flask-WTF (for form handling)
- BeautifulSoup (for web scraping)
- Requests (for HTTP requests)
- pandas (for data manipulation)
- openpyxl (for Excel export)
- SheetJS (for Excel download in the frontend)

## Installation

1. Clone the repository:

    ```bash
    git clone that-ar-guy/ou-scrapper
    cd ou-scrapper
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the Flask application:

    ```bash
    python app.py
    ```

4. Open your browser and go to:

    ```
    http://127.0.0.1:5000/
    ```

## Usage

1. Enter the following details into the form:
   - **Result Link**: URL of the result page.
   - **College Code**: The college code for your institution.
   - **Field Code**: The field code corresponding to the results.
   - **Year**: The academic year of the results.

2. Click the **Get Results** button.


3. Once the results are displayed, you can download the results as an Excel file by clicking the **Download as Excel Sheet** button.

## Example

An example result link might look like: https://ou-scrapper.onrender.com/

