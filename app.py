# app.py
import os
from datetime import datetime, date
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem,
    QHeaderView, QProgressBar, QInputDialog, QFileDialog, QDialog, QFormLayout
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QPainter

from database import (
    fetch_expenses, add_expense_to_db, delete_expense_from_db,
    get_monthly_budget, set_budget,
    fetch_incomes, add_income, delete_income,
    fetch_recurring_expenses, add_recurring_expense, delete_recurring_expense,
    backup_db, restore_db
)

CATEGORIES = ["Food", "Transportation", "Rent", "Shopping", "Entertainment", "Bills", "Other"]

class ExpenseApp(QWidget):
    def __init__(self, username=None, user_id=None):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.dark_mode = False
        self.init_ui()
        # Auto-apply recurring before first load (ensures recurring for current period present)
        self.apply_recurring_expenses()
        self.load_table_data()

    def init_ui(self):
        self.setWindowTitle(f"Expense Tracker - {self.username}")
        self.resize(900, 900)

        # Inputs
        self.date_box = QDateEdit(); self.date_box.setDate(QDate.currentDate()); self.date_box.setCalendarPopup(True)
        self.dropdown = QComboBox(); self.dropdown.addItems(CATEGORIES)
        self.amount = QLineEdit(); self.amount.setPlaceholderText("Amount")
        self.description = QLineEdit(); self.description.setPlaceholderText("Description / Notes")

        # Buttons
        self.add_button = QPushButton("Add Expense")
        self.delete_button = QPushButton("Delete Expense")
        self.export_excel_button = QPushButton("Export to Excel")
        self.export_pdf_button = QPushButton("Export to PDF")
        self.set_budget_button = QPushButton("Set Monthly Budget")
        self.toggle_dark_button = QPushButton("Toggle Dark Mode")
        self.backup_button = QPushButton("Backup DB")
        self.restore_button = QPushButton("Restore DB")
        self.recurring_button = QPushButton("Manage Recurring")
        self.income_button = QPushButton("Manage Incomes")

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Id", "Date", "Category", "Amount", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Labels + Budget
        self.total_monthly_label = QLabel()
        self.total_yearly_label = QLabel()
        self.budget_status_label = QLabel()
        self.budget_progress = QProgressBar()

        # Chart
        self.chart_view = QChartView(); self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Search / Filter controls
        self.filter_start_date = QDateEdit(); self.filter_start_date.setDate(QDate.currentDate().addMonths(-1)); self.filter_start_date.setCalendarPopup(True)
        self.filter_end_date = QDateEdit(); self.filter_end_date.setDate(QDate.currentDate()); self.filter_end_date.setCalendarPopup(True)
        self.filter_category = QComboBox(); self.filter_category.addItem("All"); self.filter_category.addItems(CATEGORIES)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("Search description...")
        self.search_button = QPushButton("Search / Filter")
        self.reset_filter_button = QPushButton("Reset Filters")

        # Connect signals
        self.add_button.clicked.connect(self.add_expense)
        self.delete_button.clicked.connect(self.delete_expense)
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.set_budget_button.clicked.connect(self.change_budget)
        self.toggle_dark_button.clicked.connect(self.toggle_dark_mode)
        self.backup_button.clicked.connect(self.do_backup)
        self.restore_button.clicked.connect(self.do_restore)
        self.recurring_button.clicked.connect(self.open_recurring_manager)
        self.income_button.clicked.connect(self.open_income_manager)
        self.search_button.clicked.connect(self.apply_filters)
        self.reset_filter_button.clicked.connect(self.load_table_data)

        # Layouts
        layout = QVBoxLayout()

        row_add = QHBoxLayout()
        row_add.addWidget(QLabel("Date:")); row_add.addWidget(self.date_box)
        row_add.addWidget(QLabel("Category:")); row_add.addWidget(self.dropdown)
        row_add.addWidget(QLabel("Amount:")); row_add.addWidget(self.amount)
        row_add.addWidget(QLabel("Description:")); row_add.addWidget(self.description)
        row_add.addWidget(self.add_button)

        row_actions = QHBoxLayout()
        row_actions.addWidget(self.delete_button); row_actions.addWidget(self.export_excel_button)
        row_actions.addWidget(self.export_pdf_button); row_actions.addWidget(self.set_budget_button)
        row_actions.addWidget(self.recurring_button); row_actions.addWidget(self.income_button)

        row_tools = QHBoxLayout()
        row_tools.addWidget(self.backup_button); row_tools.addWidget(self.restore_button); row_tools.addWidget(self.toggle_dark_button)

        row_filter = QHBoxLayout()
        row_filter.addWidget(QLabel("From:")); row_filter.addWidget(self.filter_start_date)
        row_filter.addWidget(QLabel("To:")); row_filter.addWidget(self.filter_end_date)
        row_filter.addWidget(QLabel("Category:")); row_filter.addWidget(self.filter_category)
        row_filter.addWidget(self.search_box); row_filter.addWidget(self.search_button); row_filter.addWidget(self.reset_filter_button)

        layout.addLayout(row_add); layout.addLayout(row_actions); layout.addLayout(row_tools); layout.addLayout(row_filter)
        layout.addWidget(self.table)
        layout.addWidget(self.total_monthly_label); layout.addWidget(self.total_yearly_label)
        layout.addWidget(self.budget_status_label); layout.addWidget(self.budget_progress)
        layout.addWidget(self.chart_view)

        self.setLayout(layout)
        self.apply_styles()

    def apply_styles(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget { font-family: Arial; font-size: 14px; background: #121212; color: #e0e0e0; }
                QLineEdit, QComboBox, QDateEdit { background: #1e1e1e; border: 1px solid #333; padding: 4px; color: #e0e0e0; }
                QPushButton { background: #2c2c2c; border: 1px solid #444; padding: 6px; color: #fff; }
                QTableWidget { background: #1a1a1a; }
                QProgressBar { background: #1e1e1e; border: 1px solid #333; }
            """)
        else:
            self.setStyleSheet("QWidget { font-family: Arial; font-size: 14px; }")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_styles()

    # ---------- Data ----------
    def load_table_data(self):
        expenses = fetch_expenses(self.user_id)
        self.populate_table(expenses)
        self.update_totals_and_chart(expenses)

    def populate_table(self, expenses):
        self.table.setRowCount(0)
        for row_idx, expense in enumerate(expenses):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(expense):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def apply_filters(self):
        start_date = self.filter_start_date.date().toString("yyyy-MM-dd")
        end_date = self.filter_end_date.date().toString("yyyy-MM-dd")
        category = self.filter_category.currentText()
        keyword = self.search_box.text().strip().lower()

        all_expenses = fetch_expenses(self.user_id)
        filtered = []
        for exp in all_expenses:
            exp_id, date, exp_category, amount, desc = exp
            if date < start_date or date > end_date:
                continue
            if category != "All" and exp_category != category:
                continue
            if keyword and keyword not in (desc or "").lower():
                continue
            filtered.append(exp)

        self.populate_table(filtered)
        self.update_totals_and_chart(filtered, filtered_mode=True)

    # ---------- CRUD ----------
    def add_expense(self):
        date_str = self.date_box.date().toString("yyyy-MM-dd")
        category = self.dropdown.currentText()
        amount = self.amount.text().strip()
        description = self.description.text().strip()

        if not amount or not description:
            QMessageBox.warning(self, "Input Error", "Amount and Description cannot be empty!")
            return
        try:
            float(amount)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Amount must be a number!")
            return

        if add_expense_to_db(date_str, category, amount, description, self.user_id):
            self.load_table_data()
            self.clear_inputs()
        else:
            QMessageBox.critical(self, "Error", "Failed to add expense")

    def delete_expense(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "No Selection", "Please select an expense to delete.")
            return
        expense_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete selected expense?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes and delete_expense_from_db(expense_id):
            self.load_table_data()

    def clear_inputs(self):
        self.date_box.setDate(QDate.currentDate())
        self.dropdown.setCurrentIndex(0)
        self.amount.clear()
        self.description.clear()

    # ---------- Budget ----------
    def change_budget(self):
        current = get_monthly_budget(self.user_id) or 0.0
        new_budget, ok = QInputDialog.getDouble(self, "Set Budget", "Enter new monthly budget:", float(current), 0)
        if ok:
            set_budget(self.user_id, new_budget)
            self.load_table_data()

    # ---------- Totals / Chart ----------
    def update_totals_and_chart(self, expenses, filtered_mode: bool = False):
        current_month = QDate.currentDate().toString("yyyy-MM")
        current_year = QDate.currentDate().toString("yyyy")

        total_month = 0.0
        total_year = 0.0
        category_totals = {}

        for exp in expenses:
            date = exp[1]
            category = exp[2]
            try:
                amount = float(exp[3])
            except Exception:
                amount = 0.0

            if date.startswith(current_month):
                total_month += amount
                category_totals[category] = category_totals.get(category, 0.0) + amount

            if date.startswith(current_year):
                total_year += amount

        prefix = "Filtered " if filtered_mode else ""
        self.total_monthly_label.setText(f"🟢 {prefix}Total This Month: ₹ {total_month:.2f}")
        self.total_yearly_label.setText(f"🔵 {prefix}Total This Year: ₹ {total_year:.2f}")

        budget = get_monthly_budget(self.user_id)
        if budget:
            remaining = budget - total_month
            percent = min(int((total_month / budget) * 100), 100) if budget > 0 else 0
            self.budget_status_label.setText(f"💰 Budget: ₹{budget:.2f} | Spent: ₹{total_month:.2f} | Remaining: ₹{remaining:.2f}")
            self.budget_progress.setValue(percent)
            if total_month > budget:
                self.budget_progress.setStyleSheet("QProgressBar::chunk { background: red; }")
                QMessageBox.critical(self, "⚠ Budget Exceeded", f"You have exceeded your monthly budget of ₹{budget:.2f}!\nCurrent spending: ₹{total_month:.2f}")
            elif total_month > budget * 0.8:
                self.budget_progress.setStyleSheet("QProgressBar::chunk { background: orange; }")
                QMessageBox.warning(self, "⚠ Budget Alert", f"You have used more than 80% of your monthly budget (₹{budget:.2f}).\nCurrent spending: ₹{total_month:.2f}")
            else:
                self.budget_progress.setStyleSheet("QProgressBar::chunk { background: green; }")
        else:
            self.budget_status_label.setText("💡 Set a monthly budget to track spending.")
            self.budget_progress.setValue(0)

        # Pie chart
        series = QPieSeries()
        for cat, amt in category_totals.items():
            if amt > 0:
                series.append(cat, amt)
        chart = QChart(); chart.addSeries(series)
        chart.setTitle("Spending by Category")
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart_view.setChart(chart)

    # ---------- Export ----------
    def export_to_excel(self):
        expenses = fetch_expenses(self.user_id)
        if not expenses:
            QMessageBox.information(self, "No Data", "No expenses to export.")
            return
        df = pd.DataFrame(expenses, columns=["ID", "Date", "Category", "Amount", "Description"])
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "expenses.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            df.to_excel(path, index=False)
            QMessageBox.information(self, "Export Successful", f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"{e}")

    def export_to_pdf(self):
        expenses = fetch_expenses(self.user_id)
        if not expenses:
            QMessageBox.information(self, "No Data", "No expenses to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "expenses.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        pdf = SimpleDocTemplate(path, pagesize=A4); styles = getSampleStyleSheet(); elements = []
        data = [["ID", "Date", "Category", "Amount", "Description"]]
        for exp in expenses:
            data.append([str(x) for x in exp])
        table = Table(data); table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4caf50")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ]))
        elements.append(Paragraph("Expense Report", styles["Title"])); elements.append(table)
        try:
            pdf.build(elements)
            QMessageBox.information(self, "Export Successful", f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"{e}")

    # ---------- Backup / Restore ----------
    def do_backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup Database", "expense_backup.db", "DB Files (*.db)")
        if not path: return
        if backup_db(path): QMessageBox.information(self, "Backup", f"Saved: {path}")
        else: QMessageBox.critical(self, "Backup Failed", "Could not backup.")

    def do_restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore Database", "", "DB Files (*.db)")
        if not path: return
        confirm = QMessageBox.question(self, "Confirm Restore", "Restoring will replace current data. Continue?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            if restore_db(path): QMessageBox.information(self, "Restore", "Database restored. Restart the app.")
            else: QMessageBox.critical(self, "Restore Failed", "Could not restore DB.")

    # ---------- Recurring (Auto-add) ----------
    def apply_recurring_expenses(self):
        """
        Auto-add recurring expenses for current month (Monthly) and current week (Weekly)
        If an expense with same (category, description) already exists for that period, skip.
        """
        recs = fetch_recurring_expenses(self.user_id)
        if not recs:
            return

        existing = fetch_expenses(self.user_id)
        # build set keys: (category, description, period_id)
        existing_keys = set()
        for e in existing:
            _, dt, cat, amt, desc = e
            # period keys
            yyyy_mm = dt[:7]  # 'YYYY-MM'
            # iso year-week for weekly:
            try:
                y, m, d = map(int, dt.split("-"))
                wk = date(y, m, d).isocalendar()[1]
                yyyy_week = f"{y}-W{wk}"
            except Exception:
                yyyy_week = None
            existing_keys.add(("M", cat, (desc or ""), yyyy_mm))
            if yyyy_week:
                existing_keys.add(("W", cat, (desc or ""), yyyy_week))

        for r in recs:
            rec_id, category, amount, description, interval = r
            description = description or ""
            if interval == "Monthly":
                period = QDate.currentDate().toString("yyyy-MM")
                key = ("M", category, description, period)
                if key not in existing_keys:
                    today = datetime.today().strftime("%Y-%m-%d")
                    add_expense_to_db(today, category, amount, description or f"Recurring ({category})", self.user_id)
            elif interval == "Weekly":
                qd = QDate.currentDate()
                py = qd.year(); pm = qd.month(); pd = qd.day()
                iso_week = date(py, pm, pd).isocalendar()[1]
                period = f"{py}-W{iso_week}"
                key = ("W", category, description, period)
                if key not in existing_keys:
                    today = datetime.today().strftime("%Y-%m-%d")
                    add_expense_to_db(today, category, amount, description or f"Recurring ({category})", self.user_id)

    def open_recurring_manager(self):
        dlg = RecurringExpenseManager(self.user_id, parent=self)
        dlg.exec()
        self.apply_recurring_expenses()
        self.load_table_data()

    def open_income_manager(self):
        dlg = IncomeManager(self.user_id, parent=self)
        dlg.exec()
        self.load_table_data()

# ---------- Dialogs ----------
class RecurringExpenseManager(QDialog):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Manage Recurring Expenses")
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        self.rec_table = QTableWidget(0, 5)
        self.rec_table.setHorizontalHeaderLabels(["ID", "Category", "Amount", "Description", "Interval"])
        self.rec_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.rec_table)

        form = QFormLayout()
        self.cat_box = QComboBox(); self.cat_box.addItems(CATEGORIES)
        self.amount_box = QLineEdit()
        self.desc_box = QLineEdit()
        self.interval_box = QComboBox(); self.interval_box.addItems(["Monthly", "Weekly"])
        form.addRow("Category:", self.cat_box); form.addRow("Amount:", self.amount_box)
        form.addRow("Description:", self.desc_box); form.addRow("Interval:", self.interval_box)
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.add_btn = QPushButton("Add Recurring"); self.del_btn = QPushButton("Delete Selected")
        btns.addWidget(self.add_btn); btns.addWidget(self.del_btn)
        layout.addLayout(btns)
        self.add_btn.clicked.connect(self.add_recurring); self.del_btn.clicked.connect(self.delete_selected)
        self.load_recurring()

    def load_recurring(self):
        rows = fetch_recurring_expenses(self.user_id)
        self.rec_table.setRowCount(0)
        for r in rows:
            row = self.rec_table.rowCount(); self.rec_table.insertRow(row)
            for i, val in enumerate(r):
                self.rec_table.setItem(row, i, QTableWidgetItem(str(val)))

    def add_recurring(self):
        cat = self.cat_box.currentText(); amt = self.amount_box.text().strip(); desc = self.desc_box.text().strip()
        interval = self.interval_box.currentText()
        if not amt:
            QMessageBox.warning(self, "Input", "Amount is required."); return
        try:
            float(amt)
        except ValueError:
            QMessageBox.warning(self, "Input", "Amount must be a number."); return
        if add_recurring_expense(cat, amt, desc, interval, self.user_id):
            self.load_recurring(); QMessageBox.information(self, "Saved", "Recurring expense added.")

    def delete_selected(self):
        row = self.rec_table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Select", "Select a recurring item to delete."); return
        rec_id = int(self.rec_table.item(row, 0).text())
        if delete_recurring_expense(rec_id):
            self.load_recurring()

class IncomeManager(QDialog):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Manage Incomes")
        self.resize(600, 360)
        layout = QVBoxLayout(self)
        self.inc_table = QTableWidget(0, 5)
        self.inc_table.setHorizontalHeaderLabels(["ID", "Date", "Source", "Amount", "Notes"])
        self.inc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.inc_table)

        form = QFormLayout()
        self.date_box = QDateEdit(); self.date_box.setDate(QDate.currentDate()); self.date_box.setCalendarPopup(True)
        self.source_box = QLineEdit(); self.source_box.setPlaceholderText("Salary / Freelance / Bonus")
        self.amount_box = QLineEdit(); self.notes_box = QLineEdit()
        form.addRow("Date:", self.date_box); form.addRow("Source:", self.source_box); form.addRow("Amount:", self.amount_box); form.addRow("Notes:", self.notes_box)
        layout.addLayout(form)

        btns = QHBoxLayout(); self.add_btn = QPushButton("Add Income"); self.del_btn = QPushButton("Delete Selected")
        btns.addWidget(self.add_btn); btns.addWidget(self.del_btn); layout.addLayout(btns)
        self.add_btn.clicked.connect(self.add_inc); self.del_btn.clicked.connect(self.del_inc)
        self.load_incomes()

    def load_incomes(self):
        rows = fetch_incomes(self.user_id)
        self.inc_table.setRowCount(0)
        for r in rows:
            row = self.inc_table.rowCount(); self.inc_table.insertRow(row)
            for i, val in enumerate(r):
                self.inc_table.setItem(row, i, QTableWidgetItem(str(val)))

    def add_inc(self):
        date = self.date_box.date().toString("yyyy-MM-dd"); source = self.source_box.text().strip(); amount = self.amount_box.text().strip(); notes = self.notes_box.text().strip()
        if not source or not amount:
            QMessageBox.warning(self, "Input", "Source and Amount are required."); return
        try:
            float(amount)
        except ValueError:
            QMessageBox.warning(self, "Input", "Amount must be a number."); return
        if add_income(date, source, amount, notes, self.user_id):
            self.load_incomes(); QMessageBox.information(self, "Saved", "Income added.")

    def del_inc(self):
        row = self.inc_table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Select", "Select an income to delete."); return
        inc_id = int(self.inc_table.item(row, 0).text())
        if delete_income(inc_id):
            self.load_incomes()
