#!/usr/bin/env python3
"""Track expenses and income with charts and CSV export."""

import csv
import json
import argparse
import sys
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

DATA_FILE = Path(__file__).parent / "expenses.json"
CHARTS_DIR = Path(__file__).parent / "charts"

CATEGORIES = {
    "income": ["Salary", "Freelance", "Investment", "Gift", "Other Income"],
    "expense": [
        "Food", "Transport", "Housing", "Utilities", "Entertainment",
        "Shopping", "Healthcare", "Education", "Travel", "Subscriptions", "Other",
    ],
}


def load_data() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return []


def save_data(data: list[dict]):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_entry(entry_type: str):
    print(f"\n  Add {entry_type.title()}")
    print(f"  Categories: {', '.join(CATEGORIES[entry_type])}")

    category = input("  Category: ").strip()
    if not category:
        print("  Category cannot be empty.")
        return

    amount_str = input("  Amount: $").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("  Invalid amount.")
        return

    description = input("  Description (optional): ").strip()
    date_str = input("  Date (YYYY-MM-DD, Enter for today): ").strip()
    if not date_str:
        date_str = date.today().isoformat()

    entry = {
        "type": entry_type,
        "category": category,
        "amount": amount,
        "description": description,
        "date": date_str,
        "created_at": datetime.now().isoformat(),
    }

    data = load_data()
    data.append(entry)
    save_data(data)
    print(f"  Added: ${amount:.2f} ({category})")


def show_summary(month: str | None = None):
    data = load_data()
    if not data:
        print("  No entries found.")
        return

    if month:
        data = [e for e in data if e["date"].startswith(month)]
        if not data:
            print(f"  No entries for {month}.")
            return

    income = sum(e["amount"] for e in data if e["type"] == "income")
    expenses = sum(e["amount"] for e in data if e["type"] == "expense")
    balance = income - expenses

    print(f"\n  {'=' * 45}")
    print(f"  Financial Summary{' (' + month + ')' if month else ''}")
    print(f"  {'=' * 45}")
    print(f"  Total Income:   ${income:>10,.2f}")
    print(f"  Total Expenses: ${expenses:>10,.2f}")
    print(f"  {'─' * 30}")
    print(f"  Balance:        ${balance:>10,.2f}")

    print(f"\n  --- Expense Breakdown ---")
    expense_by_cat = defaultdict(float)
    for e in data:
        if e["type"] == "expense":
            expense_by_cat[e["category"]] += e["amount"]

    for cat, amt in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
        pct = (amt / expenses * 100) if expenses > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {cat:<15} ${amt:>9,.2f} ({pct:>5.1f}%) {bar}")

    if any(e["type"] == "income" for e in data):
        print(f"\n  --- Income Breakdown ---")
        income_by_cat = defaultdict(float)
        for e in data:
            if e["type"] == "income":
                income_by_cat[e["category"]] += e["amount"]
        for cat, amt in sorted(income_by_cat.items(), key=lambda x: -x[1]):
            print(f"  {cat:<15} ${amt:>9,.2f}")


def list_entries(entry_type: str | None = None, limit: int = 20):
    data = load_data()
    if entry_type:
        data = [e for e in data if e["type"] == entry_type]

    data = sorted(data, key=lambda x: x["date"], reverse=True)[:limit]

    if not data:
        print("  No entries found.")
        return

    print(f"\n  {'Date':<12} {'Type':<8} {'Category':<15} {'Amount':>10} Description")
    print(f"  {'-' * 70}")
    for e in data:
        sign = "+" if e["type"] == "income" else "-"
        print(f"  {e['date']:<12} {e['type']:<8} {e['category']:<15} {sign}${e['amount']:>9,.2f} {e.get('description', '')}")


def generate_charts():
    if not HAS_MATPLOTLIB:
        print("  matplotlib is required for charts. Install with: pip install matplotlib")
        return

    data = load_data()
    if not data:
        print("  No data to chart.")
        return

    CHARTS_DIR.mkdir(exist_ok=True)

    expense_by_cat = defaultdict(float)
    for e in data:
        if e["type"] == "expense":
            expense_by_cat[e["category"]] += e["amount"]

    if expense_by_cat:
        fig, ax = plt.subplots(figsize=(10, 6))
        cats = list(expense_by_cat.keys())
        vals = list(expense_by_cat.values())
        colors = plt.cm.Set3(range(len(cats)))
        wedges, texts, autotexts = ax.pie(vals, labels=cats, autopct="%1.1f%%", colors=colors, startangle=90)
        ax.set_title("Expense Distribution by Category", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / "expense_pie.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: charts/expense_pie.png")

    monthly = defaultdict(lambda: {"income": 0, "expense": 0})
    for e in data:
        month_key = e["date"][:7]
        monthly[month_key][e["type"]] += e["amount"]

    if monthly:
        months = sorted(monthly.keys())
        incomes = [monthly[m]["income"] for m in months]
        expenses_list = [monthly[m]["expense"] for m in months]

        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(months))
        width = 0.35
        ax.bar([i - width / 2 for i in x], incomes, width, label="Income", color="#2ecc71")
        ax.bar([i + width / 2 for i in x], expenses_list, width, label="Expenses", color="#e74c3c")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount ($)")
        ax.set_title("Monthly Income vs Expenses", fontsize=14, fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / "monthly_bar.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: charts/monthly_bar.png")

    daily_expense = defaultdict(float)
    for e in data:
        if e["type"] == "expense":
            daily_expense[e["date"]] += e["amount"]

    if daily_expense:
        dates = sorted(daily_expense.keys())
        cumulative = []
        total = 0
        for d in dates:
            total += daily_expense[d]
            cumulative.append(total)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.fill_between(range(len(dates)), cumulative, alpha=0.3, color="#3498db")
        ax.plot(range(len(dates)), cumulative, color="#3498db", linewidth=2)
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Expense ($)")
        ax.set_title("Cumulative Expenses Over Time", fontsize=14, fontweight="bold")
        step = max(1, len(dates) // 10)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45)
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / "cumulative_expense.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: charts/cumulative_expense.png")

    print("  Charts generated!")


def export_csv(filepath: str):
    data = load_data()
    if not data:
        print("  No data to export.")
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "type", "category", "amount", "description"])
        writer.writeheader()
        for e in sorted(data, key=lambda x: x["date"]):
            writer.writerow({k: e.get(k, "") for k in writer.fieldnames})
    print(f"  Exported {len(data)} entries to {filepath}")


def add_sample_data():
    """Add sample data for demonstration."""
    import random

    samples = [
        ("income", "Salary", 5000, "Monthly salary"),
        ("expense", "Housing", 1500, "Rent"),
        ("expense", "Food", 450, "Groceries"),
        ("expense", "Transport", 120, "Gas"),
        ("expense", "Utilities", 200, "Electric + Internet"),
        ("expense", "Entertainment", 80, "Netflix + Spotify"),
        ("expense", "Shopping", 250, "Amazon orders"),
        ("expense", "Healthcare", 150, "Insurance"),
        ("income", "Freelance", 800, "Side project"),
        ("expense", "Food", 180, "Restaurants"),
        ("expense", "Subscriptions", 50, "Cloud services"),
        ("expense", "Education", 30, "Udemy course"),
        ("expense", "Travel", 350, "Weekend trip"),
    ]

    data = load_data()
    for month_offset in range(3):
        month = f"2025-{(1 + month_offset):02d}"
        for entry_type, category, base_amount, desc in samples:
            amount = round(base_amount * random.uniform(0.8, 1.2), 2)
            day = random.randint(1, 28)
            data.append({
                "type": entry_type,
                "category": category,
                "amount": amount,
                "description": desc,
                "date": f"{month}-{day:02d}",
                "created_at": datetime.now().isoformat(),
            })
    save_data(data)
    print(f"  Added {len(samples) * 3} sample entries across 3 months.")


def main():
    parser = argparse.ArgumentParser(description="Expense Tracker with Charts")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("add-income", help="Add income entry")
    subparsers.add_parser("add-expense", help="Add expense entry")

    summary_p = subparsers.add_parser("summary", help="Show financial summary")
    summary_p.add_argument("--month", help="Filter by month (YYYY-MM)")

    list_p = subparsers.add_parser("list", help="List entries")
    list_p.add_argument("--type", choices=["income", "expense"], help="Filter by type")
    list_p.add_argument("--limit", type=int, default=20, help="Number of entries")

    subparsers.add_parser("charts", help="Generate charts")

    export_p = subparsers.add_parser("export", help="Export to CSV")
    export_p.add_argument("filepath", help="Output CSV file path")

    subparsers.add_parser("sample", help="Add sample data for demo")

    args = parser.parse_args()

    if args.command == "add-income":
        add_entry("income")
    elif args.command == "add-expense":
        add_entry("expense")
    elif args.command == "summary":
        show_summary(args.month)
    elif args.command == "list":
        list_entries(args.type, args.limit)
    elif args.command == "charts":
        generate_charts()
    elif args.command == "export":
        export_csv(args.filepath)
    elif args.command == "sample":
        add_sample_data()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
