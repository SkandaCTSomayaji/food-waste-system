\# Food Waste Management System



A web app that connects food donors (restaurants, hotels, events) with NGOs to reduce food waste.



\## Features

\- Role-based accounts: Donor, NGO, Admin

\- Donors post surplus food with quantity, expiry, photo, and GPS location

\- NGOs claim and collect food; listings auto-expire

\- Contact numbers shared only between matched donor and NGO

\- Admin impact dashboard (kg saved vs wasted)

\- CSRF protection, hashed passwords, role-based access control



\## Tech Stack

Flask, PostgreSQL, SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Pillow, Bootstrap 5



\## Run locally

1\. `python -m venv venv` and activate it

2\. `pip install -r requirements.txt`

3\. Copy `.env.example` to `.env` and fill in your values

4\. `flask --app run db upgrade`

5\. `python create\_admin.py` (creates the admin account)

6\. `python run.py`



