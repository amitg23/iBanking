# iBanking

A local Python banking desktop app for creating customers, opening checking and savings accounts, searching by name or account number, and recording deposits.

## Features
- Add a customer with first name, last name, date of birth, address, SSN, and initial deposit
- Mask SSNs in the UI and stored data
- Validate required fields and input formats
- Generate unique 6-digit account numbers
- Search by first name, last name, or account number
- View checking and savings account details and transaction history
- Delete a selected customer and their accounts after confirmation
- Save all data in a local JSON store under the data directory

## Project structure
- banking_app.py: desktop UI entry point
- core/banking_core.py: business logic and JSON storage layer
- data/customers.json: local customer/account records
- tests/test_banking_app.py: validation tests

## Run the app
From the project root:

1. Create a virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

2. Install dependencies
   python -m pip install --upgrade pip

3. Launch the application
   python banking_app.py

To retrieve an account without relying on the desktop accessibility tree:

python banking_app.py --account 505576

For machine-readable output:

python banking_app.py --account 505576 --json

## Notes
- The app does not connect to any external database or service.
- All banking data is stored locally in JSON files under the data folder.
- If your Python installation is missing Tkinter support, install the system Tk library before running the GUI.

## Validate the app
Run the automated tests:

source .venv/bin/activate
python -m pytest -q
