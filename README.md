# TaskFlow

TaskFlow is a Flask-based smart task management app with:

- user registration and login
- task create, edit, delete, cancel, and restore
- PostgreSQL storage
- analytics powered by Pandas and NumPy
- live task updates with Flask-SocketIO
- HTML, CSS, and vanilla JavaScript frontend

## Features

- authentication with register, login, logout
- task dashboard with filters, search, and sorting
- inline status updates from the task card
- due date and priority visible on every task
- overdue tasks highlighted automatically
- double-click a task card to open edit mode
- cancelled tasks are restore-only and appear only in the `Cancelled` view
- `All Tasks` is sorted by due date first, then priority

## Tech Stack

- Python 3.13
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-SocketIO
- PostgreSQL
- SQLAlchemy
- Pandas
- NumPy

## Project Structure

```text
smart-task-manager/
|-- app/
|   |-- __init__.py
|   |-- models/
|   |-- routes/
|   `-- utils/
|-- static/
|   |-- css/
|   `-- js/
|-- templates/
|   |-- auth/
|   `-- tasks/
|-- init_db.py
|-- README.md
|-- requirements.txt
|-- run.py
|-- run_windows.ps1
|-- schema.sql
`-- setup_windows.ps1
```

## Requirements

Before starting, make sure you have:

- Python `3.13.x`
- PostgreSQL installed and running
- a PostgreSQL user account you know the password for

## Quick Start on Windows

If you are on Windows and want the shortest setup path:

### 1. Run first-time setup

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

This script:

- creates `.venv` if missing
- upgrades `pip`
- installs dependencies
- reminds you to create `.env` if it is missing

### 2. Create your PostgreSQL database

You can do this in `pgAdmin` or in SQL.

Example database name:

```text
task_manager_db
```

### 3. Create `.env`

Create a file named `.env` in the project root and paste:

```env
SECRET_KEY=change-me
FLASK_ENV=development
FLASK_DEBUG=True
HOST=127.0.0.1
PORT=5000
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/task_manager_db
SOCKETIO_ASYNC_MODE=threading
```

Replace:

- `postgres` with your PostgreSQL username if different
- `your_postgres_password` with the real PostgreSQL password
- `task_manager_db` with your real database name

Important:

- this is the PostgreSQL password, not your app login password
- if your password contains special characters like `@`, `:`, `/`, `#`, or `%`, it should be URL-encoded

### 4. Initialize the database

```powershell
.\.venv\Scripts\python.exe init_db.py
```

### 5. Start the app

```powershell
powershell -ExecutionPolicy Bypass -File .\run_windows.ps1
```

Or directly:

```powershell
.\.venv\Scripts\python.exe run.py
```

### 6. Open the app

```text
http://127.0.0.1:5000
```

## Manual Setup

Use this if you want to do everything yourself instead of the helper scripts.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create `.env`

Create a file named `.env` in the project root with:

```env
SECRET_KEY=change-me
FLASK_ENV=development
FLASK_DEBUG=True
HOST=127.0.0.1
PORT=5000
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/task_manager_db
SOCKETIO_ASYNC_MODE=threading
```

Then update `DATABASE_URL` with your real PostgreSQL username, password, and database name.

### 4. Create the PostgreSQL database

Example SQL:

```sql
CREATE DATABASE task_manager_db;
```

If you prefer `pgAdmin`:

1. Open `pgAdmin`
2. Connect to your PostgreSQL server
3. Right-click `Databases`
4. Click `Create` -> `Database...`
5. Enter `task_manager_db`
6. Save

### 5. Initialize the database

```powershell
python init_db.py
```

### 6. Run the app

```powershell
python run.py
```

## Windows Helper Scripts

### `setup_windows.ps1`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

What it does:

- creates `.venv` if missing
- upgrades `pip`
- installs packages from `requirements.txt`
- reminds you to create `.env` if missing

### `run_windows.ps1`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_windows.ps1
```

What it does:

- checks that `.venv` exists
- checks that `.env` exists
- starts the app with `.venv\Scripts\python.exe`

## Environment Variables

Example `.env`:

```env
SECRET_KEY=change-me
FLASK_ENV=development
FLASK_DEBUG=True
HOST=127.0.0.1
PORT=5000
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/task_manager_db
SOCKETIO_ASYNC_MODE=threading
```

## Database Schema

This project includes a PostgreSQL schema file for assignment submission:

```text
schema.sql
```

You can create your tables with:

```powershell
psql -U postgres -d task_manager_db -f schema.sql
```

Or you can continue using:

```powershell
python init_db.py
```

## Running the App Later

After first-time setup, your usual flow is:

```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_windows.ps1
```

## App Behavior

### Task views

- `All Tasks` shows active tasks only
- cancelled tasks appear only in the `Cancelled` page
- cancelled tasks cannot be edited
- cancelled tasks can be restored with a restore button

### Sorting

- `All Tasks` is sorted by due date first
- tasks with the same due-date order are then sorted by priority
- tasks with no due date are pushed below tasks that do have one

### Editing

- click `Edit` to edit a task
- double-click a task card to open edit mode
- status can be changed directly from the task card

### Visual indicators

- priority is shown on each task
- due date is shown on each task
- overdue active tasks are highlighted in red

## API Overview

### Task endpoints

- `GET /api/tasks/`
- `GET /api/tasks/<id>`
- `POST /api/tasks/`
- `PUT /api/tasks/<id>`
- `DELETE /api/tasks/<id>`

### Analytics endpoint

- `GET /api/analytics/`

## Common Issues

### `password authentication failed for user "postgres"`

This means your `DATABASE_URL` is pointing to PostgreSQL correctly, but the username or password is wrong.

Check:

- PostgreSQL is running
- username in `.env` is correct
- password in `.env` is the real PostgreSQL password
- database name in `.env` exists

Example:

```env
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/task_manager_db
```

### `ModuleNotFoundError` or missing packages

Run:

```powershell
pip install -r requirements.txt
```

Or rerun:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

### `python init_db.py` fails

Check:

- PostgreSQL is running
- `DATABASE_URL` is correct
- the database already exists

### App starts but you do not see DB changes reflected

Refresh the page once after restarting the app so the browser picks up the latest JavaScript and styles.

## Notes About Python 3.13

This project is set up to run well on Windows with Python `3.13`:

- Socket.IO uses `threading` mode
- you do not need `eventlet`
- dependency versions are compatible with Python `3.13`

## Assignment Coverage

This project covers:

- authentication
- REST API CRUD for tasks
- PostgreSQL persistence
- analytics with Pandas and NumPy
- live updates with Flask-SocketIO
- frontend UI with HTML, CSS, and JavaScript
