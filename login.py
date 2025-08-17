# login.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from database import check_login, create_user, get_security_question, reset_password_with_answer
from app import ExpenseApp

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Expense Tracker")
        self.setGeometry(700, 300, 360, 260)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        title = QLabel("Expense Tracker — Login / Register")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        self.login_btn = QPushButton("Login")
        self.register_btn = QPushButton("Register")
        self.forgot_btn = QPushButton("Forgot Password")

        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)
        layout.addWidget(self.forgot_btn)

        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)
        self.forgot_btn.clicked.connect(self.forgot_password)

    def login(self):
        uname = self.username.text().strip()
        passwd = self.password.text().strip()
        if not uname or not passwd:
            QMessageBox.warning(self, "Input Error", "Username and Password are required.")
            return

        user_id = check_login(uname, passwd)
        if user_id:
            self.expense_app = ExpenseApp(username=uname, user_id=user_id)
            self.expense_app.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")

    def register(self):
        from PyQt6.QtWidgets import QInputDialog

        uname = self.username.text().strip()
        passwd = self.password.text().strip()
        if not uname or not passwd:
            QMessageBox.warning(self, "Input Error", "Username and Password cannot be empty.")
            return

        question, ok = QInputDialog.getText(self, "Security Question", "Enter a security question (used for password reset):")
        if not ok:
            return
        answer, ok = QInputDialog.getText(self, "Security Answer", "Enter the answer to the question (case-insensitive):")
        if not ok:
            return

        if create_user(uname, passwd, question, answer):
            QMessageBox.information(self, "Success", "Registration successful. You can now log in.")
        else:
            QMessageBox.warning(self, "Failed", "Username already exists.")

    def forgot_password(self):
        from PyQt6.QtWidgets import QInputDialog

        uname, ok = QInputDialog.getText(self, "Forgot Password", "Enter your username:")
        if not ok or not uname:
            return

        question = get_security_question(uname)
        if not question:
            QMessageBox.warning(self, "Not Found", "User not found or no security question set.")
            return

        answer, ok = QInputDialog.getText(self, "Security Question", question)
        if not ok or not answer:
            return

        new_pw, ok = QInputDialog.getText(self, "Reset Password", "Enter new password:")
        if not ok or not new_pw:
            return

        if reset_password_with_answer(uname, answer, new_pw):
            QMessageBox.information(self, "Success", "Password has been reset. Please login.")
        else:
            QMessageBox.critical(self, "Failed", "Security answer incorrect.")
