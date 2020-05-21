![INSPECT Logo](/images/header.png)

# INSPECT app
A specimen to results data tracking tool for SEARCH SARS-CoV-2 tests. The application is used by technicians to track testing samples as they are plated, reformatted, and finally tested by storing specimen and plate barcode information. The app is currently hosted here:
http://inspect-covid.com/accounts/login/?next=/qpcr_records/

# How it works
INSPECT app is a web-based application written in the django framework.

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