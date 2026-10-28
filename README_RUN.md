# Tour Package — Final Run Instructions

Run these commands from the project root, the folder that contains `run.py`.

## Install dependencies on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, open a Command Prompt and use `.venv\Scripts\activate.bat` instead.

## Run the complete automated test suite

```powershell
python -m unittest discover -s tests -v
```

A passing suite ends with `OK`. If a test fails, read the first failure and fix it before merging. Run tests after the other three Day 5 PRs have been merged.

## Start the website

```powershell
python run.py
```

Open `http://127.0.0.1:5000` in a browser. Stop the local server with `Ctrl+C` in the terminal.

## Local development admin account

- Email: `admin@tour.local`
- Password: `Admin123!`

This is only a demo account for local coursework. Do not use these credentials for a deployed website.

## Manual final checklist

1. Open the package catalogue and test the city filter.
2. Open a package and confirm its image, dates, duration, rating, and price appear clearly.
3. Sign in as a customer, book a package, and confirm it appears under My bookings.
4. Confirm that same customer no longer sees the active booking in the catalogue.
5. Reschedule the booking, then cancel it; confirm the cancelled booking stays in history and the package returns to the catalogue.
6. Sign in as admin and add a package with at least one destination.
7. Sign in as a customer and confirm they cannot access admin pages.

Only describe tests as passed after actually running them.
