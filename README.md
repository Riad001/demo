# Cloud-Based Expense Tracking and Customer Analytics Dashboard

This project is a working prototype for a single cinema branch dashboard that follows the proposal in the dissertation document: "Cloud-Based Expense Tracking and Customer Analytics Dashboard for a Single Cinema Branch." It focuses on expense tracking, daily operating analysis, customer spending behaviour, and financial reporting for a cinema branch.

## Project goals

- Track ticket sales, concession revenue, memberships, parking, and operating expenses.
- Visualize daily revenue and cost performance.
- Analyse customer segments and spending behaviour.
- Support management decisions with a simple reporting workflow.
- Deliver a prototype that can be deployed to a cloud environment such as Google Cloud with a managed MySQL database.

## Included features

- Dashboard overview with KPI cards.
- Revenue vs expense trend chart across 14 simulated days.
- Expense breakdown by category.
- Customer segment analysis.
- Daily operating summary table.
- CSV export of the financial report.
- SQLite-backed prototype data layer with an architecture ready for cloud migration.

## Tech stack

- Python 3
- Flask
- SQLite for local development
- HTML/CSS/JavaScript
- Chart.js for visual analytics
- Optional production path: Google Cloud + MySQL / Cloud SQL

## Run locally

1. Open a terminal in the project folder.
2. Create and activate a virtual environment.
3. Install the requirements:

   pip install -r requirements.txt

4. Start the app:

   python app.py

5. Open the browser at:

   http://localhost:5000/

## Project structure

- app.py — Flask application and data setup
- templates/index.html — dashboard UI
- static/style.css — dashboard styling
- static/script.js — optional client logic (not required for the main dashboard)
- data/cinema_branch.db — generated SQLite database file
- requirements.txt — Python dependencies

## Data model

The prototype uses realistic simulated data for:

- Daily ticket sales
- concession and parking revenue
- membership income
- daily operating expenses by category
- customer segment behaviour and satisfaction scores

This keeps the prototype realistic while avoiding confidential cinema financial data.

## Deployment notes

The app is built as a prototype, and the data layer is intentionally designed to be portable. For production on Google Cloud, the same schema can be migrated to a Cloud SQL MySQL instance while retaining the same business logic.

## Planned evaluation criteria

The prototype addresses the proposal's evaluation criteria:

- Dashboard response time
- Accuracy of expense calculations
- Data visualization effectiveness
- usability of the interface
- ability to generate financial reports
- reliability of customer spending analysis
