from flask import Flask, render_template, request
from forms import ResultForm
from bs4 import BeautifulSoup
import mechanize
import requests
from requests.adapters import HTTPAdapter
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///results.db'
db = SQLAlchemy(app)

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

# Web Scraping Function
def scrape_results(result_link, college_code, field_code, year):
    globalbr = mechanize.Browser()
    globalbr.set_handle_robots(False)
    pre_link = result_link + "?mbstatus&htno="
    results = []

    for index in range(1, 121):  # Regular students
        hall_ticket = f"{college_code}{year}{field_code}{str(index).zfill(3)}"
        result = find_result(globalbr, pre_link, hall_ticket)
        if result:
            results.append(result)

    for index in range(301, 313):  # Lateral entry students
        hall_ticket = f"{college_code}{year}{field_code}{str(index).zfill(3)}"
        result = find_result(globalbr, pre_link, hall_ticket)
        if result:
            results.append(result)

    return results

# Helper Function to Find Result
def find_result(globalbr, pre_link, hall_ticket):
    result_link = pre_link + hall_ticket
    session = requests.Session()
    adapter = HTTPAdapter()
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    raw = session.get(result_link)
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
    rows = table.find_all("tr")[-1]
    marks = rows.find_all('td')[1].get_text(strip=True)

    f_grade_subjects = extract_subjects_with_f_grade(soup)

    return {
        'hall_ticket': hall_ticket,
        'marks': marks,
        'name': name,
        'backlogs': Markup('<br>'.join(f_grade_subjects)) if f_grade_subjects else "No Backlogs",
    }

# Helper Function to Extract 'F' Grade Subjects
def extract_subjects_with_f_grade(soup):
    table = soup.find(id="AutoNumber4")
    if not table:
        return []
    rows = table.find_all("tr")[1:]
    f_grade_subjects = [
        f"{row.find_all('td')[0].text.strip()} - {row.find_all('td')[1].text.strip()}"
        for row in rows if row.find_all("td")[4].text.strip() in ['F', 'Ab']
    ]
    return f_grade_subjects

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

        # Scraping Results
        results = scrape_results(result_link, college_code, field_code, year)

    return render_template('index.html', form=form, results=results, college_name=college_name, field_name=field_name)

if __name__ == '__main__':
    app.run(debug=True)
