# Expense Tracker with Charts

Track income and expenses with category breakdowns, charts, and CSV export.

## Features

- Add income and expense entries with categories
- Financial summary with category breakdown
- Pie chart for expense distribution
- Bar chart for monthly income vs expenses
- Cumulative expense line chart
- CSV export
- Sample data generator for demo

## Usage

```bash
pip install -r requirements.txt

# Add sample data for demo
python main.py sample

# Add entries
python main.py add-income
python main.py add-expense

# View summary
python main.py summary
python main.py summary --month 2025-01

# List entries
python main.py list
python main.py list --type expense --limit 10

# Generate charts
python main.py charts

# Export to CSV
python main.py export expenses.csv
```
