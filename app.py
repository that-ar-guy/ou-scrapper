from collections import Counter
from flask import Flask, render_template, request,session
from forms import ResultForm
from bs4 import BeautifulSoup
import mechanize
import requests
from requests.adapters import HTTPAdapter
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
import logging
import os
# added code
from flask import jsonify
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///results.db'
db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Models
class StudentResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hall_ticket = db.Column(db.String(10), nullable=False)
    marks = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    backlogs = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'{self.name} - {self.hall_ticket}'


FIELD_CHOICES = {
    '748': 'AIML',
    '749': 'IOT',
    '750': 'DS',
    '736': 'MECH',
    '733': 'CSE',
    '732': 'CIVIL',
    '737': 'IT',
    '735': 'ECE',
    '734': 'EEE',
}

COLLEGE_CHOICES = {
    '1604': 'MJCET',
    '1603': 'DECCAN',
    '1605': 'ISL',
    '1610': 'NSAKCET',
    '2455': 'KMEC',
    '2453': 'NGIT',
}

# Web Scraping Function (Batch Processing)
def scrape_results_in_batches(result_link, college_code, field_code, year):
    globalbr = mechanize.Browser()
    globalbr.set_handle_robots(False)
    pre_link = result_link + "?mbstatus&htno="

    results = []
    BATCH_SIZE = 30  # Scrape in smaller batches to reduce memory load

    # Regular students (batched)
    for batch_start in range(1, 121, BATCH_SIZE):
        results += scrape_batch(globalbr, pre_link, college_code, field_code, year, batch_start, batch_start + BATCH_SIZE)

    # Lateral entry students (batched)
    for batch_start in range(301, 320, BATCH_SIZE):
        results += scrape_batch(globalbr, pre_link, college_code, field_code, year, batch_start, batch_start + BATCH_SIZE)

    return results


# Helper Function to Scrape Each Batch
def scrape_batch(globalbr, pre_link, college_code, field_code, year, batch_start, batch_end):
    results = []
    
    with requests.Session() as session:
        adapter = HTTPAdapter()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        for index in range(batch_start, batch_end):
            hall_ticket = f"{college_code}{year}{field_code}{str(index).zfill(3)}"
            app.logger.info(f"Scraping hall ticket: {hall_ticket}")
            result = find_result(globalbr, pre_link, hall_ticket, session)
            if result:
                results.append(result)

    return results

# Helper Function to Find Result
def find_result(globalbr, pre_link, hall_ticket, session):
    result_link = pre_link + hall_ticket
    try:
        raw = session.get(result_link, timeout=5)
        raw.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching result for {hall_ticket}: {e}")
        return None

    soup = BeautifulSoup(raw.content, "html.parser")

    table = soup.find('table', id="AutoNumber3")
    if not table:
        return None

    last_row = table("tr")[2]
    td_list = last_row.find_all("td")
    name = td_list[1].text

    table = soup.find(id="AutoNumber5")
    if not table:
        return None
    rows = table.find_all("tr")[2:]  # Assuming multiple rows for different semesters

    # Create a list of dictionaries for marks across semesters
    marks_list = []
    for row in rows:
        cells = row.find_all("td")
        semester = cells[0].get_text(strip=True)
        marks = cells[1].get_text(strip=True)
        marks_list.append({'semester': semester, 'marks': marks})

    f_grade_subjects = extract_subjects_with_f_grade(soup)
    cleared_subjects = extract_cleared_subjects(soup)

    return {
        'hall_ticket': hall_ticket,
        'marks': marks_list,  # List of dictionaries with semester and marks
        'name': name,
        'backlogs': Markup('<br>'.join(f_grade_subjects)) if f_grade_subjects else "No Backlogs",
        'cleared_subjects': Markup('<br>'.join(cleared_subjects)) if cleared_subjects else "No Cleared Subjects",
    }

# Helper Function to Extract 'F' Grade Subjects
def extract_subjects_with_f_grade(soup):
    table = soup.find(id="AutoNumber4")
    if not table:
        return []
    rows = table.find_all("tr")[1:]
    f_grade_subjects = [
        f"{row.find_all('td')[0].text.strip()} - {row.find_all('td')[1].text.strip()}"
        for row in rows if row.find_all("td")[3].text.strip() in ['F', 'Ab']
    ]
    return f_grade_subjects

#subjects without f or ab grade
def extract_cleared_subjects(soup):
    table = soup.find(id="AutoNumber4")
    if not table:
        return []

    rows = table.find_all("tr")[1:]  # Skip the header row
    cleared_subjects = []

    for row in rows:
        cells = row.find_all("td")
        subject_code = cells[0].text.strip()
        subject_name = cells[1].text.strip()
        grade = cells[3].text.strip()

        if subject_code == "Code" and subject_name == "Subject":
            continue

        if grade not in ['F', 'Ab']:  # Only include subjects without F or Ab grades
            cleared_subjects.append(f"{subject_code} - {subject_name}")

    return cleared_subjects

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    form = ResultForm(request.form)
    results = []
    college_name = None
    field_name = None

    if request.method == 'POST' and form.validate():
        result_link = form.result_link.data
        college_code = form.college_code.data
        college_name = COLLEGE_CHOICES.get(college_code)
        field_code = form.field_code.data
        field_name = FIELD_CHOICES.get(field_code)
        year = form.year.data
                
        # Scraping Results in batches
        results = scrape_results_in_batches(result_link, college_code, field_code, year)
        session['results'] = results
    return render_template('index.html', form=form, results=results, college_name=college_name, field_name=field_name)

@app.route('/analysis')
def analysis():
    results = session.get('results', [])
    
    # Collect all backlogs excluding "No Backlogs"
    all_backlogs = []
    for result in results:
        if result['backlogs'] != "No Backlogs":
            all_backlogs.extend(result['backlogs'].split('<br>'))  # Assuming backlogs are split by <br>
    
    # Count occurrences of each backlog and sort by count in descending order
    backlog_counts = dict(sorted(Counter(all_backlogs).items(), key=lambda item: item[1], reverse=True))
    
    return render_template('analysis.html', backlog_counts=backlog_counts)


if __name__ == '__main__':
    app.run(debug=True)
