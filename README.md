![INSPECT Logo](/images/header.png)

# INSPECT app
A specimen to results data tracking tool for SEARCH SARS-CoV-2 tests. The application is used by technicians to track testing samples as they are plated, reformatted, and finally tested by storing specimen and plate barcode information. The app is currently hosted here:
http://inspect-covid.com/qpcr_records/

# How it works
INSPECT app is a web-based application written in the django framework.

# Requirements
Module 	Version
pandas 	0.20.1
pybedtools 	0.7.8
asgiref  3.2.7
bokeh  2.0.2 (required if you want to display a dashboard counter)
boto3  1.13.6
botocore  1.16.6
coverage  5.1
Django  3.0.5
django-crispy-forms  1.9.0
django-storages  1.9.1
django-tables2  2.3.1
docutils  0.15.2
Jinja2  2.11.2
jmespath  0.9.5
MarkupSafe  1.1.1
numpy  1.18.4
packaging  20.4
pandas  1.0.3
Pillow  7.1.2
psycopg2  2.8.5 (required if you want to use a postgres database)
pyparsing  2.4.7
python-dateutil  2.8.1
python-decouple  3.3
pytz  2020.1
PyYAML  5.3.1
s3transfer  0.3.3
six  1.14.0
sqlparse  0.3.1
tablib  1.1.0
tornado  6.0.4
typing-extensions  3.7.4.2
urllib3 1.25.9
xlrd  1.2.0

# Installation
```
git clone https://github.com/shassathe/covid_qPCR_test.git
pip install -r requirements.txt
```

# Setup
In the covid_qPCR_test directory:
```
python manage.py migrate
python manage.py createsuperuser
```
Create super-user credentials for app management

To start the server on localhost:
```
python manage.py runserver
```
