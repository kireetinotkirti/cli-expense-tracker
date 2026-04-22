#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║         💰 CLI Expense Tracker v1.0                  ║
║         Track • Categorize • Export                  ║
╚══════════════════════════════════════════════════════╝
Features:
  - Add, view, edit, delete expenses
  - Categorize expenses
  - Filter by date, category, amount
  - Monthly & category summaries
  - CSV export / import
  - Colored terminal output (no external libs needed)
"""

import csv
import os
import sys
import json
from datetime import datetime, date
from collections import defaultdict

# ─── ANSI Colors (no external libraries needed) ──────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_BLUE = "\033[44m"
    BG_GREEN= "\033[42m"

def colored(text, color):
    return f"{color}{text}{C.RESET}"

def bold(text):
    return f"{C.BOLD}{text}{C.RESET}"

# ─── Constants ────────────────────────────────────────────────────────────────

DATA_FILE = "expenses.json"
CSV_FILE  = "expenses_export.csv"

CATEGORIES = [
    "🍔 Food & Dining",
    "🚗 Transport",
    "🛒 Groceries",
    "🏠 Housing & Rent",
    "💡 Utilities",
    "🎬 Entertainment",
    "👗 Clothing",
    "💊 Health & Medical",
    "📚 Education",
    "✈️  Travel",
    "💼 Work & Business",
    "🎁 Gifts & Donations",
    "📱 Subscriptions",
    "🏋️  Fitness",
    "🛠️  Maintenance",
    "💰 Savings & Investment",
    "🐾 Pets",
    "🧴 Personal Care",
    "📦 Other",
]

CATEGORY_COLORS = {
    "🍔 Food & Dining":       C.YELLOW,
    "🚗 Transport":           C.CYAN,
    "🛒 Groceries":           C.GREEN,
    "🏠 Housing & Rent":      C.BLUE,
    "💡 Utilities":           C.MAGENTA,
    "🎬 Entertainment":       C.RED,
    "👗 Clothing":            C.MAGENTA,
    "💊 Health & Medical":    C.GREEN,
    "📚 Education":           C.CYAN,
    "✈️  Travel":             C.YELLOW,
    "💼 Work & Business":     C.BLUE,
    "🎁 Gifts & Donations":   C.RED,
    "📱 Subscriptions":       C.CYAN,
    "🏋️  Fitness":            C.GREEN,
    "🛠️  Maintenance":        C.YELLOW,
    "💰 Savings & Investment": C.GREEN,
    "🐾 Pets":                C.MAGENTA,
    "🧴 Personal Care":       C.CYAN,
    "📦 Other":               C.WHITE,
}

# ─── Data Layer ───────────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_data(expenses):
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2)

def next_id(expenses):
    return max((e["id"] for e in expenses), default=0) + 1

# ─── Display Helpers ──────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print(colored("╔══════════════════════════════════════════════════════╗", C.CYAN))
    print(colored("║", C.CYAN) + colored("         💰  CLI EXPENSE TRACKER  v1.0               ", C.BOLD) + colored("║", C.CYAN))
    print(colored("║", C.CYAN) + colored("              Track • Categorize • Export             ", C.DIM) + colored("║", C.CYAN))
    print(colored("╚══════════════════════════════════════════════════════╝", C.CYAN))
    print()

def divider(char="─", width=56, color=C.DIM):
    print(colored(char * width, color))

def pause():
    input(colored("\n  Press Enter to continue...", C.DIM))

def fmt_amount(amount):
    return colored(f"₹{amount:,.2f}", C.GREEN)

def fmt_date(d):
    return colored(d, C.CYAN)

def fmt_category(cat):
    color = CATEGORY_COLORS.get(cat, C.WHITE)
    return colored(cat, color)

def print_expense_row(e, index=None):
    prefix = f"  [{index}] " if index is not None else "  "
    print(f"{prefix}{fmt_date(e['date'])}  {fmt_amount(e['amount']):>18}  {fmt_category(e['category'])}")
    if e.get("description"):
        print(colored(f"       📝 {e['description']}", C.DIM))

def print_expenses_table(expenses, title="All Expenses"):
    if not expenses:
        print(colored("  No expenses found.", C.DIM))
        return
    print()
    print(bold(f"  {title}"))
    divider()
    print(colored(f"  {'ID':<5} {'Date':<12} {'Amount':>12}  Category", C.DIM))
    divider()
    total = 0
    for e in expenses:
        color = CATEGORY_COLORS.get(e["category"], C.WHITE)
        id_str   = colored(f"  #{e['id']:<4}", C.DIM)
        date_str = colored(f"{e['date']:<12}", C.CYAN)
        amt_str  = colored(f"₹{e['amount']:>10,.2f}", C.GREEN)
        cat_str  = colored(e["category"], color)
        print(f"{id_str} {date_str} {amt_str}  {cat_str}")
        if e.get("description"):
            print(colored(f"             📝 {e['description']}", C.DIM))
        total += e["amount"]
    divider()
    print(colored(f"  {'TOTAL':>29} ₹{total:,.2f}", C.BOLD + C.YELLOW))
    print()

# ─── Input Helpers ────────────────────────────────────────────────────────────

def prompt(label, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        val = input(colored(f"  {label}{suffix}: ", C.CYAN)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default or ""
    return val if val else (default or "")

def prompt_float(label, default=None):
    while True:
        raw = prompt(label, str(default) if default else None)
        try:
            val = float(raw)
            if val <= 0:
                print(colored("  ⚠  Amount must be positive.", C.YELLOW))
                continue
            return round(val, 2)
        except ValueError:
            print(colored("  ⚠  Enter a valid number (e.g. 250 or 1299.50).", C.YELLOW))

def prompt_date(label="Date", default=None):
    if default is None:
        default = date.today().strftime("%Y-%m-%d")
    while True:
        raw = prompt(f"{label} (YYYY-MM-DD)", default)
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print(colored("  ⚠  Invalid date. Use YYYY-MM-DD format.", C.YELLOW))

def pick_category(current=None):
    print()
    print(bold("  Select Category:"))
    for i, cat in enumerate(CATEGORIES, 1):
        color = CATEGORY_COLORS.get(cat, C.WHITE)
        marker = colored("◀ current", C.DIM) if cat == current else ""
        print(f"  {colored(str(i).rjust(2), C.DIM)}. {colored(cat, color)} {marker}")
    print()
    while True:
        raw = prompt("Category number", str(CATEGORIES.index(current) + 1) if current in CATEGORIES else "19")
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(CATEGORIES):
                return CATEGORIES[idx]
            print(colored(f"  ⚠  Enter a number between 1 and {len(CATEGORIES)}.", C.YELLOW))
        except ValueError:
            print(colored("  ⚠  Enter a valid number.", C.YELLOW))

def confirm(msg):
    ans = prompt(f"{msg} (y/n)", "n")
    return ans.lower() in ("y", "yes")

# ─── Core Features ────────────────────────────────────────────────────────────

def add_expense(expenses):
    clear()
    banner()
    print(bold("  ➕  Add New Expense"))
    divider()

    amount      = prompt_float("Amount (₹)")
    exp_date    = prompt_date()
    category    = pick_category()
    description = prompt("Description (optional)")

    expense = {
        "id":          next_id(expenses),
        "amount":      amount,
        "date":        exp_date,
        "category":    category,
        "description": description,
        "created_at":  datetime.now().isoformat(),
    }
    expenses.append(expense)
    save_data(expenses)

    print()
    divider(color=C.GREEN)
    print(colored("  ✅  Expense added successfully!", C.GREEN))
    print(f"  {fmt_date(exp_date)}  {fmt_amount(amount)}  {fmt_category(category)}")
    divider(color=C.GREEN)
    pause()

def view_expenses(expenses):
    clear()
    banner()
    print(bold("  📋  View Expenses"))
    divider()
    print(colored("  Filter by:", C.DIM))
    print("   1. All expenses")
    print("   2. By date range")
    print("   3. By category")
    print("   4. By month")
    print("   5. Search by description")
    print()
    choice = prompt("Option", "1")

    filtered = expenses[:]

    if choice == "2":
        start = prompt_date("Start date", "2024-01-01")
        end   = prompt_date("End date",   date.today().strftime("%Y-%m-%d"))
        filtered = [e for e in filtered if start <= e["date"] <= end]
        title = f"Expenses from {start} to {end}"

    elif choice == "3":
        cat = pick_category()
        filtered = [e for e in filtered if e["category"] == cat]
        title = f"Expenses — {cat}"

    elif choice == "4":
        month = prompt("Month (YYYY-MM)", datetime.today().strftime("%Y-%m"))
        filtered = [e for e in filtered if e["date"].startswith(month)]
        title = f"Expenses for {month}"

    elif choice == "5":
        keyword = prompt("Search keyword").lower()
        filtered = [e for e in filtered if keyword in e.get("description", "").lower()]
        title = f"Expenses matching '{keyword}'"

    else:
        title = "All Expenses"

    filtered.sort(key=lambda e: e["date"], reverse=True)
    print_expenses_table(filtered, title)
    pause()

def edit_expense(expenses):
    clear()
    banner()
    print(bold("  ✏️   Edit Expense"))
    divider()

    recent = sorted(expenses, key=lambda e: e["date"], reverse=True)[:10]
    print_expenses_table(recent, "Recent Expenses (choose one to edit)")

    raw = prompt("Enter Expense ID to edit")
    try:
        eid = int(raw)
    except ValueError:
        print(colored("  ⚠  Invalid ID.", C.YELLOW))
        pause()
        return

    target = next((e for e in expenses if e["id"] == eid), None)
    if not target:
        print(colored(f"  ⚠  Expense #{eid} not found.", C.YELLOW))
        pause()
        return

    print()
    print(colored("  Leave blank to keep current value.", C.DIM))
    divider()

    target["amount"]      = prompt_float("Amount (₹)", target["amount"])
    target["date"]        = prompt_date("Date", target["date"])
    target["category"]    = pick_category(target["category"])
    target["description"] = prompt("Description", target.get("description", ""))
    target["updated_at"]  = datetime.now().isoformat()

    save_data(expenses)
    print()
    print(colored("  ✅  Expense updated!", C.GREEN))
    pause()

def delete_expense(expenses):
    clear()
    banner()
    print(bold("  🗑️   Delete Expense"))
    divider()

    recent = sorted(expenses, key=lambda e: e["date"], reverse=True)[:10]
    print_expenses_table(recent, "Recent Expenses")

    raw = prompt("Enter Expense ID to delete")
    try:
        eid = int(raw)
    except ValueError:
        print(colored("  ⚠  Invalid ID.", C.YELLOW))
        pause()
        return

    target = next((e for e in expenses if e["id"] == eid), None)
    if not target:
        print(colored(f"  ⚠  Expense #{eid} not found.", C.YELLOW))
        pause()
        return

    print()
    print_expense_row(target)
    print()

    if confirm(colored("  ⚠  Are you sure you want to delete this expense?", C.RED)):
        expenses.remove(target)
        save_data(expenses)
        print(colored("  ✅  Expense deleted.", C.GREEN))
    else:
        print(colored("  Cancelled.", C.DIM))
    pause()

def summary(expenses):
    clear()
    banner()
    print(bold("  📊  Summary & Analytics"))
    divider()

    if not expenses:
        print(colored("  No expenses to summarize.", C.DIM))
        pause()
        return

    print("  1. Monthly summary")
    print("  2. Category summary")
    print("  3. Overall stats")
    print()
    choice = prompt("Option", "1")

    if choice == "1":
        monthly = defaultdict(float)
        for e in expenses:
            month = e["date"][:7]
            monthly[month] += e["amount"]

        print()
        print(bold("  📅  Monthly Spending"))
        divider()
        grand = 0
        for month in sorted(monthly, reverse=True):
            amt = monthly[month]
            grand += amt
            bar_len = int(amt / max(monthly.values()) * 30)
            bar = colored("█" * bar_len, C.GREEN) + colored("░" * (30 - bar_len), C.DIM)
            print(f"  {colored(month, C.CYAN)}  {bar}  {colored(f'₹{amt:,.2f}', C.YELLOW)}")
        divider()
        print(colored(f"  Grand Total: ₹{grand:,.2f}", C.BOLD + C.GREEN))

    elif choice == "2":
        cat_totals = defaultdict(float)
        cat_counts = defaultdict(int)
        for e in expenses:
            cat_totals[e["category"]] += e["amount"]
            cat_counts[e["category"]] += 1

        total = sum(cat_totals.values())
        print()
        print(bold("  🏷️   Spending by Category"))
        divider()
        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        for cat, amt in sorted_cats:
            pct = (amt / total * 100) if total else 0
            color = CATEGORY_COLORS.get(cat, C.WHITE)
            bar_len = int(pct / 100 * 25)
            bar = colored("█" * bar_len, color) + colored("░" * (25 - bar_len), C.DIM)
            count_str = colored(f"({cat_counts[cat]} items)", C.DIM)
            print(f"  {colored(cat, color):<35} {bar}  {colored(f'₹{amt:,.2f}', C.YELLOW)} {colored(f'{pct:.1f}%', C.DIM)} {count_str}")
        divider()
        print(colored(f"  Total: ₹{total:,.2f}", C.BOLD + C.GREEN))

    else:
        amounts = [e["amount"] for e in expenses]
        total   = sum(amounts)
        avg     = total / len(amounts)
        highest = max(expenses, key=lambda e: e["amount"])
        lowest  = min(expenses, key=lambda e: e["amount"])
        dates   = sorted(e["date"] for e in expenses)

        print()
        print(bold("  📈  Overall Statistics"))
        divider()
        stats = [
            ("Total Expenses",   f"₹{total:,.2f}"),
            ("Total Records",    str(len(expenses))),
            ("Average Expense",  f"₹{avg:,.2f}"),
            ("Highest Expense",  f"₹{highest['amount']:,.2f} ({highest['category']})"),
            ("Lowest Expense",   f"₹{lowest['amount']:,.2f} ({lowest['category']})"),
            ("Date Range",       f"{dates[0]}  →  {dates[-1]}"),
            ("Categories Used",  str(len(set(e["category"] for e in expenses)))),
        ]
        for label, val in stats:
            print(f"  {colored(label + ':', C.DIM):<30} {colored(val, C.GREEN)}")

    print()
    pause()

def export_csv(expenses):
    clear()
    banner()
    print(bold("  📤  Export to CSV"))
    divider()

    if not expenses:
        print(colored("  No expenses to export.", C.DIM))
        pause()
        return

    filename = prompt("Export filename", CSV_FILE)
    if not filename.endswith(".csv"):
        filename += ".csv"

    fields = ["id", "date", "amount", "category", "description", "created_at"]
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for e in sorted(expenses, key=lambda x: x["date"]):
                writer.writerow(e)
        print()
        print(colored(f"  ✅  Exported {len(expenses)} records to '{filename}'", C.GREEN))
        print(colored(f"  📁  Location: {os.path.abspath(filename)}", C.DIM))
    except IOError as err:
        print(colored(f"  ❌  Export failed: {err}", C.RED))
    pause()

def import_csv(expenses):
    clear()
    banner()
    print(bold("  📥  Import from CSV"))
    divider()

    filename = prompt("CSV filename to import", CSV_FILE)
    if not os.path.exists(filename):
        print(colored(f"  ❌  File '{filename}' not found.", C.RED))
        pause()
        return

    imported = 0
    skipped  = 0
    existing_ids = {e["id"] for e in expenses}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    eid = int(row.get("id", 0))
                    amt = float(row.get("amount", 0))
                    if amt <= 0:
                        skipped += 1
                        continue
                    if eid in existing_ids:
                        eid = next_id(expenses)

                    expense = {
                        "id":          eid,
                        "amount":      round(amt, 2),
                        "date":        row.get("date", date.today().strftime("%Y-%m-%d")),
                        "category":    row.get("category", "📦 Other"),
                        "description": row.get("description", ""),
                        "created_at":  row.get("created_at", datetime.now().isoformat()),
                    }
                    expenses.append(expense)
                    existing_ids.add(eid)
                    imported += 1
                except (ValueError, KeyError):
                    skipped += 1

        save_data(expenses)
        print()
        print(colored(f"  ✅  Imported: {imported} records", C.GREEN))
        if skipped:
            print(colored(f"  ⚠   Skipped:  {skipped} invalid rows", C.YELLOW))
    except IOError as err:
        print(colored(f"  ❌  Import failed: {err}", C.RED))
    pause()

def delete_all(expenses):
    clear()
    banner()
    print(bold(colored("  ⚠️   Delete ALL Expenses", C.RED)))
    divider()
    print(colored(f"  This will permanently delete {len(expenses)} expense(s).", C.RED))
    print()
    if confirm(colored("  Type 'y' to confirm PERMANENT deletion", C.RED)):
        expenses.clear()
        save_data(expenses)
        print(colored("  ✅  All expenses deleted.", C.GREEN))
    else:
        print(colored("  Cancelled.", C.DIM))
    pause()

# ─── Main Menu ────────────────────────────────────────────────────────────────

def main_menu(expenses):
    clear()
    banner()

    total = sum(e["amount"] for e in expenses)
    today_total = sum(e["amount"] for e in expenses if e["date"] == date.today().strftime("%Y-%m-%d"))
    month_total = sum(e["amount"] for e in expenses if e["date"].startswith(datetime.today().strftime("%Y-%m")))

    # Stats bar
    print(colored("  ┌────────────────────────────────────────────────────┐", C.DIM))
    print(f"  │  📅 Today: {colored(f'₹{today_total:,.2f}', C.GREEN):<25} 📆 Month: {colored(f'₹{month_total:,.2f}', C.YELLOW)}", end="")
    print(colored("│", C.DIM))
    print(f"  │  💾 Records: {colored(str(len(expenses)), C.CYAN):<24} 💰 Total: {colored(f'₹{total:,.2f}', C.GREEN)}", end="")
    print(colored(" │", C.DIM))
    print(colored("  └────────────────────────────────────────────────────┘", C.DIM))
    print()

    menu_items = [
        ("1", "➕  Add Expense",         C.GREEN),
        ("2", "📋  View / Filter Expenses", C.CYAN),
        ("3", "✏️   Edit Expense",         C.YELLOW),
        ("4", "🗑️   Delete Expense",       C.RED),
        ("5", "📊  Summary & Analytics",  C.MAGENTA),
        ("6", "📤  Export to CSV",        C.CYAN),
        ("7", "📥  Import from CSV",      C.CYAN),
        ("8", "⚠️   Delete ALL Expenses",  C.RED),
        ("0", "🚪  Exit",                 C.DIM),
    ]

    for key, label, color in menu_items:
        print(f"  {colored(key, C.BOLD + color)}  {colored(label, color)}")

    print()
    return prompt("Choose option")

# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    # Windows color support
    if os.name == "nt":
        os.system("color")

    expenses = load_data()

    actions = {
        "1": add_expense,
        "2": view_expenses,
        "3": edit_expense,
        "4": delete_expense,
        "5": summary,
        "6": export_csv,
        "7": import_csv,
        "8": delete_all,
    }

    while True:
        try:
            choice = main_menu(expenses)
            if choice == "0":
                clear()
                print()
                print(colored("  👋  Thanks for using Expense Tracker! Goodbye.", C.CYAN))
                print()
                sys.exit(0)
            elif choice in actions:
                actions[choice](expenses)
            else:
                print(colored("  ⚠  Invalid option. Please choose 0–8.", C.YELLOW))
                pause()
        except KeyboardInterrupt:
            print()
            print(colored("\n  👋  Goodbye!", C.CYAN))
            print()
            sys.exit(0)

if __name__ == "__main__":
    main()
