# login.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from app import ExpenseApp
from database import check_login, create_user

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Expense Tracker")
        self.setGeometry(700, 300, 300, 200)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_btn = QPushButton("Login")
        self.register_btn = QPushButton("Register")

        layout.addWidget(QLabel("Login to continue"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)
        self.setLayout(layout)

        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)

    def login(self):
        uname = self.username.text().strip()
        passwd = self.password.text().strip()

        user_id = check_login(uname, passwd)
        if user_id:
            self.expense_app = ExpenseApp(username=uname, user_id=user_id)
            self.expense_app.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")

    def register(self):
        uname = self.username.text().strip()
        passwd = self.password.text().strip()

        if not uname or not passwd:
            QMessageBox.warning(self, "Input Error", "Username and Password cannot be empty.")
            return

        if create_user(uname, passwd):
            QMessageBox.information(self, "Success", "Registration successful. You can now log in.")
        else:
            QMessageBox.warning(self, "Failed", "Username already exists.")
