import csv
import io
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, Response, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "cinema_branch.db"

app = Flask(__name__)
app.config["DATABASE"] = str(DB_PATH)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            tickets_sold INTEGER NOT NULL,
            ticket_revenue REAL NOT NULL,
            concession_revenue REAL NOT NULL,
            membership_revenue REAL NOT NULL,
            parking_revenue REAL NOT NULL,
            total_visitors INTEGER NOT NULL,
            avg_ticket_price REAL NOT NULL,
            peak_hour INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expense_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            segment TEXT NOT NULL,
            visitors INTEGER NOT NULL,
            spend_per_person REAL NOT NULL,
            satisfaction_score REAL NOT NULL
        )
        """
    )
    conn.commit()

    if conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()[0] == 0:
        seed_demo_data(conn)
    conn.close()


def seed_demo_data(conn: sqlite3.Connection) -> None:
    start_date = datetime(2026, 5, 1)
    categories = [
        ("Utilities", 1800, "Electricity and HVAC costs"),
        ("Staffing", 4200, "Front-of-house and projection staff"),
        ("Maintenance", 960, "Projector and screen maintenance"),
        ("Inventory", 1260, "Concession stock and packaging"),
        ("Marketing", 780, "Campaigns and local promotions"),
        ("Cleaning", 520, "Cinema cleaning and supplies"),
        ("Security", 330, "Surveillance and access support"),
    ]

    for offset in range(14):
        current_day = start_date + timedelta(days=offset)
        date_str = current_day.strftime("%Y-%m-%d")
        ticket_count = 180 + (offset * 8) + (offset % 3) * 18
        ticket_revenue = round(ticket_count * (11.5 + (offset % 5) * 0.7), 2)
        concession_revenue = round(ticket_revenue * (0.44 + (offset % 4) * 0.03), 2)
        membership_revenue = round(110 + (offset * 6) + (offset % 2) * 25, 2)
        parking_revenue = round(55 + (offset * 4) + (offset % 3) * 10, 2)
        total_visitors = ticket_count + 25 + (offset % 5) * 18
        avg_ticket_price = round(ticket_revenue / ticket_count, 2)
        peak_hour = 18 + (offset % 4)

        conn.execute(
            """
            INSERT INTO daily_metrics (
                date, tickets_sold, ticket_revenue, concession_revenue,
                membership_revenue, parking_revenue, total_visitors,
                avg_ticket_price, peak_hour
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date_str,
                ticket_count,
                ticket_revenue,
                concession_revenue,
                membership_revenue,
                parking_revenue,
                total_visitors,
                avg_ticket_price,
                peak_hour,
            ),
        )

        for category, base_amount, notes in categories:
            variation = 0.65 + ((offset + len(category)) % 4) * 0.18
            amount = round(base_amount * variation, 2)
            conn.execute(
                "INSERT INTO expense_entries (date, category, amount, notes) VALUES (?, ?, ?, ?)",
                (date_str, category, amount, notes),
            )

        segments = [
            ("Families", 42 + offset * 2, 28.5 + offset * 0.4, 4.4),
            ("Students", 30 + offset, 19.5 + offset * 0.2, 4.1),
            ("Couples", 24 + offset * 2, 32.0 + offset * 0.5, 4.6),
            ("Premium Guests", 10 + offset, 48.0 + offset * 0.8, 4.8),
        ]
        for segment, visitors, spend, satisfaction in segments:
            conn.execute(
                "INSERT INTO customer_insights (date, segment, visitors, spend_per_person, satisfaction_score) VALUES (?, ?, ?, ?, ?)",
                (date_str, segment, visitors, spend, satisfaction),
            )

    conn.commit()


def get_overview() -> dict:
    conn = get_db_connection()
    revenue_row = conn.execute(
        """
        SELECT
            ROUND(COALESCE(SUM(ticket_revenue + concession_revenue + membership_revenue + parking_revenue), 0), 2) AS total_revenue,
            SUM(tickets_sold) AS tickets_sold,
            SUM(total_visitors) AS total_visitors,
            ROUND(COALESCE(AVG(avg_ticket_price), 0), 2) AS avg_ticket_price,
            ROUND(COALESCE(AVG(peak_hour), 0), 2) AS average_peak_hour
        FROM daily_metrics
        """
    ).fetchone()
    expense_row = conn.execute(
        "SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS total_expenses FROM expense_entries"
    ).fetchone()
    conn.close()

    total_revenue = float(revenue_row["total_revenue"] or 0)
    total_expenses = float(expense_row["total_expenses"] or 0)
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": round(total_revenue - total_expenses, 2),
        "tickets_sold": int(revenue_row["tickets_sold"] or 0),
        "total_visitors": int(revenue_row["total_visitors"] or 0),
        "average_ticket_price": float(revenue_row["avg_ticket_price"] or 0),
        "average_peak_hour": float(revenue_row["average_peak_hour"] or 0),
        "avg_spend_per_visitor": round(total_revenue / max(1, int(revenue_row["total_visitors"] or 0)), 2),
    }


def get_daily_metrics() -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT date, tickets_sold, ticket_revenue, concession_revenue,
               membership_revenue, parking_revenue, total_visitors,
               avg_ticket_price, peak_hour
        FROM daily_metrics
        ORDER BY date ASC
        """
    ).fetchall()

    records = []
    for row in rows:
        total_revenue = (
            float(row["ticket_revenue"])
            + float(row["concession_revenue"])
            + float(row["membership_revenue"])
            + float(row["parking_revenue"])
        )
        total_expense = conn.execute(
            "SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS daily_expense FROM expense_entries WHERE date = ?",
            (row["date"],),
        ).fetchone()["daily_expense"]
        records.append(
            {
                "date": row["date"],
                "tickets_sold": row["tickets_sold"],
                "total_revenue": round(total_revenue, 2),
                "total_expenses": round(float(total_expense or 0), 2),
                "net_profit": round(total_revenue - float(total_expense or 0), 2),
                "total_visitors": row["total_visitors"],
                "avg_ticket_price": row["avg_ticket_price"],
                "peak_hour": row["peak_hour"],
            }
        )
    conn.close()
    return records


def get_expense_breakdown() -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT category, ROUND(COALESCE(SUM(amount), 0), 2) AS total FROM expense_entries GROUP BY category ORDER BY total DESC"
    ).fetchall()
    conn.close()
    return [{"category": row["category"], "total": float(row["total"]) } for row in rows]


def get_customer_segments() -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT segment,
               SUM(visitors) AS visitors,
               ROUND(COALESCE(AVG(spend_per_person), 0), 2) AS avg_spend,
               ROUND(COALESCE(AVG(satisfaction_score), 0), 2) AS satisfaction
        FROM customer_insights
        GROUP BY segment ORDER BY visitors DESC
        """
    ).fetchall()
    conn.close()
    return [{"segment": row["segment"], "visitors": int(row["visitors"] or 0), "avg_spend": float(row["avg_spend"] or 0), "satisfaction": float(row["satisfaction"] or 0)} for row in rows]


def build_csv_report() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "date",
        "tickets_sold",
        "ticket_revenue",
        "concession_revenue",
        "membership_revenue",
        "parking_revenue",
        "total_expenses",
        "net_profit",
    ])

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT d.date, d.tickets_sold, d.ticket_revenue, d.concession_revenue,
               d.membership_revenue, d.parking_revenue,
               ROUND(COALESCE(SUM(e.amount), 0), 2) AS total_expenses
        FROM daily_metrics d
        LEFT JOIN expense_entries e ON e.date = d.date
        GROUP BY d.date, d.tickets_sold, d.ticket_revenue, d.concession_revenue,
                 d.membership_revenue, d.parking_revenue
        ORDER BY d.date ASC
        """
    ).fetchall()
    conn.close()

    for row in rows:
        total_revenue = float(row["ticket_revenue"]) + float(row["concession_revenue"]) + float(row["membership_revenue"]) + float(row["parking_revenue"])
        total_expense = float(row["total_expenses"] or 0)
        writer.writerow([
            row["date"],
            row["tickets_sold"],
            round(row["ticket_revenue"], 2),
            round(row["concession_revenue"], 2),
            round(row["membership_revenue"], 2),
            round(row["parking_revenue"], 2),
            round(total_expense, 2),
            round(total_revenue - total_expense, 2),
        ])
    return output.getvalue()


init_db()


@app.route("/")
def index():
    summary = get_overview()
    daily = get_daily_metrics()
    expenses = get_expense_breakdown()
    segments = get_customer_segments()
    return render_template(
        "index.html",
        summary=summary,
        daily=daily,
        expenses=expenses,
        segments=segments,
    )


@app.route("/api/overview")
def api_overview():
    return jsonify(
        {
            "summary": get_overview(),
            "daily": get_daily_metrics(),
            "expenses": get_expense_breakdown(),
            "segments": get_customer_segments(),
        }
    )


@app.route("/api/report")
def api_report():
    csv_data = build_csv_report()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cinema_financial_report.csv"},
    )


@app.route("/health")
def healthcheck():
    return jsonify({"status": "ok", "database": app.config["DATABASE"]})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
