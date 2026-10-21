# Tour Package — Task 1: App Foundation and Authentication

This is the first implementation task for the MSE800 Object-Oriented Project. It provides a runnable Flask foundation, SQLite persistence, customer signup/signin, signout, a protected dashboard, and an admin-only placeholder page. Package cards, booking inventory, cancellation, and package creation are planned for later tasks.

## Requirements
- Python 3.10 or newer
- pip

## Run on Windows (VS Code terminal)
Open a terminal in this folder and run:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

If PowerShell blocks activation, use Command Prompt in VS Code, or run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and then `.venv\Scripts\python.exe run.py`.

Open the local URL printed in the terminal, usually http://127.0.0.1:5000.

## Test accounts and behaviour
- Customer: create an account through **Create account**. Customer accounts are created with the `customer` role and cannot choose admin access.
- Local demo admin: `admin@tour.local` / `Admin123!`
- The local admin account is only for development. Change/remove it before any deployment or public hosting.
- The database is automatically created at `instance/tour_package.sqlite3`.

## Object-oriented design note
`app/models.py` defines the `User` model and its account lookup, creation, and authentication methods. Routes use that model rather than asking users to write SQL themselves.

## First-task acceptance checklist
- [ ] The landing page opens.
- [ ] A customer can create an account.
- [ ] A customer can sign out and sign back in.
- [ ] Incorrect credentials are rejected.
- [ ] A normal customer cannot open `/admin`.
- [ ] The demo admin can sign in and open `/admin`.

## Next task
Add the tour-package data model and package cards, including destination image, dates, cost, rating, and the **Get Package** action.
