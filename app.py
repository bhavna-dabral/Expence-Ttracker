# app.py

import datetime
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QPainter

from database import fetch_expenses, add_expense_to_db, delete_expense_from_db


class ExpenseApp(QWidget):
    def __init__(self, username=None, user_id=None):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.init_ui()
        self.load_table_data()

    def init_ui(self):
        self.setWindowTitle("Expense Tracker 2.0")
        self.resize(600, 700)

        self.date_box = QDateEdit()
        self.date_box.setDate(QDate.currentDate())
        self.dropdown = QComboBox()
        self.amount = QLineEdit()
        self.description = QLineEdit()

        self.add_button = QPushButton("Add Expense")
        self.delete_button = QPushButton("Delete Expense")
        self.export_excel_button = QPushButton("Export to Excel")
        self.export_pdf_button = QPushButton("Export to PDF")

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Id", "Date", "Category", "Amount", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.add_button.clicked.connect(self.add_expense)
        self.delete_button.clicked.connect(self.delete_expense)
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)

        self.setup_layout()
        self.populate_dropdown()
        self.apply_styles()

        # Extra UI for totals and pie chart
        self.total_monthly_label = QLabel()
        self.total_yearly_label = QLabel()
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.layout().addWidget(self.total_monthly_label)
        self.layout().addWidget(self.total_yearly_label)
        self.layout().addWidget(self.chart_view)

    def setup_layout(self):
        layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row3 = QHBoxLayout()

        row1.addWidget(QLabel("Date:"))
        row1.addWidget(self.date_box)
        row1.addWidget(QLabel("Category:"))
        row1.addWidget(self.dropdown)

        row2.addWidget(QLabel("Amount:"))
        row2.addWidget(self.amount)
        row2.addWidget(QLabel("Description:"))
        row2.addWidget(self.description)

        row3.addWidget(self.add_button)
        row3.addWidget(self.delete_button)
        row3.addWidget(self.export_excel_button)
        row3.addWidget(self.export_pdf_button)

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def populate_dropdown(self):
        categories = ["Food", "Transportation", "Rent", "Shopping", "Entertainment", "Bills", "Other"]
        self.dropdown.addItems(categories)

    def apply_styles(self):
        self.setStyleSheet("""QWidget { font-family: Arial; font-size: 14px; }""")

    def load_table_data(self):
        expenses = fetch_expenses(self.user_id)
        self.table.setRowCount(0)
        for row_idx, expense in enumerate(expenses):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(expense):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
        self.update_totals_and_chart()

    def add_expense(self):
        date = self.date_box.date().toString("yyyy-MM-dd")
        category = self.dropdown.currentText()
        amount = self.amount.text()
        description = self.description.text()

        if not amount or not description:
            QMessageBox.warning(self, "Input Error", "Amount and Description cannot be empty!")
            return

        if add_expense_to_db(date, category, amount, description, self.user_id):
            self.load_table_data()
            self.clear_inputs()
        else:
            QMessageBox.critical(self, "Error", "Failed to add expense")

    def delete_expense(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select an expense to delete.")
            return

        expense_id = int(self.table.item(selected_row, 0).text())
        confirm = QMessageBox.question(
            self, "Confirm", "Are you sure you want to delete this expense?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes and delete_expense_from_db(expense_id):
            self.load_table_data()

    def clear_inputs(self):
        self.date_box.setDate(QDate.currentDate())
        self.dropdown.setCurrentIndex(0)
        self.amount.clear()
        self.description.clear()

    def update_totals_and_chart(self):
        expenses = fetch_expenses(self.user_id)
        current_month = QDate.currentDate().toString("yyyy-MM")
        current_year = QDate.currentDate().toString("yyyy")

        total_month = 0.0
        total_year = 0.0
        category_totals = {}

        for exp in expenses:
            date = exp[1]
            category = exp[2]
            amount = float(exp[3])

            if date.startswith(current_month):
                total_month += amount
                category_totals[category] = category_totals.get(category, 0.0) + amount

            if date.startswith(current_year):
                total_year += amount

        self.total_monthly_label.setText(f"🟢 Total This Month: ₹ {total_month:.2f}")
        self.total_yearly_label.setText(f"🔵 Total This Year: ₹ {total_year:.2f}")

        # Pie chart
        series = QPieSeries()
        for cat, amt in category_totals.items():
            series.append(cat, amt)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Spending by Category")
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart_view.setChart(chart)

    def export_to_excel(self):
        expenses = fetch_expenses(self.user_id)
        df = pd.DataFrame(expenses, columns=["ID", "Date", "Category", "Amount", "Description"])
        try:
            df.to_excel("expenses.xlsx", index=False)
            QMessageBox.information(self, "Export Successful", "Expenses exported to 'expenses.xlsx'")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    def export_to_pdf(self):
        expenses = fetch_expenses(self.user_id)
        pdf = SimpleDocTemplate("expenses.pdf", pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        data = [["ID", "Date", "Category", "Amount", "Description"]]
        for exp in expenses:
            data.append([str(x) for x in exp])

        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4caf50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))

        elements.append(Paragraph("Expense Report", styles["Title"]))
        elements.append(table)

        try:
            pdf.build(elements)
            QMessageBox.information(self, "Export Successful", "Expenses exported to 'expenses.pdf'")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")
