# database.py

from PyQt6.QtSql import QSqlDatabase, QSqlQuery

def init_db(db_name):
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName(db_name)
    if not database.open():
        return False

    query = QSqlQuery()
    query.exec("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    query.exec("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    return True

def fetch_expenses(user_id=None):
    if user_id:
        query = QSqlQuery()
        query.prepare("SELECT id, date, category, amount, description FROM expenses WHERE user_id = ? ORDER BY date DESC")
        query.addBindValue(user_id)
        query.exec()
    else:
        query = QSqlQuery("SELECT * FROM expenses ORDER BY date DESC")

    expenses = []
    while query.next():
        expenses.append([query.value(i) for i in range(5)])
    return expenses

def add_expense_to_db(date, category, amount, description, user_id):
    query = QSqlQuery()
    query.prepare("""
        INSERT INTO expenses (date, category, amount, description, user_id)
        VALUES (?, ?, ?, ?, ?)
    """)
    query.addBindValue(date)
    query.addBindValue(category)
    query.addBindValue(float(amount))
    query.addBindValue(description)
    query.addBindValue(user_id)
    return query.exec()

def delete_expense_from_db(expense_id):
    query = QSqlQuery()
    query.prepare("DELETE FROM expenses WHERE id = ?")
    query.addBindValue(expense_id)
    return query.exec()

def check_login(username, password):
    query = QSqlQuery()
    query.prepare("SELECT id FROM users WHERE username = ? AND password = ?")
    query.addBindValue(username)
    query.addBindValue(password)
    query.exec()
    if query.next():
        return query.value(0)
    return None

def create_user(username, password):
    query = QSqlQuery()
    query.prepare("INSERT INTO users (username, password) VALUES (?, ?)")
    query.addBindValue(username)
    query.addBindValue(password)
    return query.exec()
