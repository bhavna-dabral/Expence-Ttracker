# main.py

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from database import init_db
from login import LoginWindow

def main():
    app = QApplication(sys.argv)

    if not init_db("expense.db"):
        QMessageBox.critical(None, "Error", "Could not open your database")
        sys.exit(1)

    login = LoginWindow()
    login.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
