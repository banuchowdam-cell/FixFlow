# FixFlow – Beginner-friendly working web prototype

A small Flask + SQLite demo for campus/hostel maintenance complaints.

## 1. Install Python
Install Python 3.10 or newer from https://www.python.org/downloads/.
During installation on Windows, tick **Add Python to PATH**.

## 2. Open the project folder in VS Code
Extract `FixFlow_Prototype.zip`, then open the extracted `fixflow_prototype` folder in VS Code.

## 3. Open the terminal in VS Code
Run these commands:

### Windows
```bash
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 4. Open the website
Visit http://127.0.0.1:5000 in your browser.

## 5. Demo logins
- Student: username `student`, password `student123`
- Maintenance staff: username `staff`, password `staff123`
- Admin: username `admin`, password `admin123`

## 6. Demonstrate the workflow
1. Log in as student.
2. Click **Report an issue**.
3. Submit a sample complaint (e.g. water leakage in Hostel Block A).
4. Log out and log in as staff.
5. Change the complaint status from Reported to In Progress.
6. Log out and log in as admin or student to show the updated dashboard.

## Notes
- The database file `fixflow.db` is created automatically the first time the app runs.
- Three sample complaints are included to make the dashboard look populated.
- Uploaded images are stored in the `uploads` folder.
- This is an educational demonstration, not a production-ready service. Before real deployment, add secure user registration, hashed passwords, CSRF protection, stronger validation, HTTPS, backups, and proper role management.
- The demo credentials and secret key are for local demonstration only. Do not use them for a public deployment.
