# database.py
import os
import shutil
import sqlite3
from typing import List, Tuple, Optional
import bcrypt

DB_NAME = "expense.db"

def _conn():
    return sqlite3.connect(DB_NAME)

def init_db(db_name: str = DB_NAME) -> bool:
    global DB_NAME
    DB_NAME = db_name
    try:
        conn = _conn()
        cur = conn.cursor()

        # Users with security question/answer (answers hashed)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            security_question TEXT,
            security_answer BLOB
        )
        """)

        # Expenses
        cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Incomes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Budgets (monthly per user)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            user_id INTEGER PRIMARY KEY,
            monthly_budget REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Recurring expenses
        cur.execute("""
        CREATE TABLE IF NOT EXISTS recurring_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            interval TEXT NOT NULL,   -- 'Monthly' or 'Weekly'
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("DB init error:", e)
        return False

# ---------- Users ----------
def create_user(username: str, password: str, security_question: Optional[str] = None, security_answer: Optional[str] = None) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        hashed_ans = bcrypt.hashpw(security_answer.lower().encode("utf-8"), bcrypt.gensalt()) if security_answer else None
        cur.execute(
            "INSERT INTO users (username, password, security_question, security_answer) VALUES (?,?,?,?)",
            (username, hashed_pw, security_question, hashed_ans)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(username: str, password: str) -> Optional[int]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        user_id, hashed = row
        if bcrypt.checkpw(password.encode("utf-8"), hashed):
            return user_id
    return None

def get_security_question(username: str) -> Optional[str]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT security_question FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def reset_password_with_answer(username: str, answer: str, new_password: str) -> bool:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT security_answer FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row or not row[0]:
        conn.close()
        return False
    stored = row[0]
    if bcrypt.checkpw(answer.lower().encode("utf-8"), stored):
        hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        cur.execute("UPDATE users SET password=? WHERE username=?", (hashed_pw, username))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# ---------- Expenses ----------
def fetch_expenses(user_id: int) -> List[Tuple]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, date, category, amount, description FROM expenses WHERE user_id=? ORDER BY date DESC, id DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def add_expense_to_db(date: str, category: str, amount: float, description: str, user_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO expenses (date, category, amount, description, user_id) VALUES (?,?,?,?,?)",
            (date, category, float(amount), description, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print("Add expense error:", e)
        return False
    finally:
        conn.close()

def delete_expense_from_db(expense_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()
        return True
    except Exception as e:
        print("Delete expense error:", e)
        return False
    finally:
        conn.close()

# ---------- Incomes ----------
def fetch_incomes(user_id: int) -> List[Tuple]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, date, source, amount, notes FROM incomes WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def add_income(date: str, source: str, amount: float, notes: str, user_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO incomes (date, source, amount, notes, user_id) VALUES (?,?,?,?,?)",
            (date, source, float(amount), notes, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print("Add income error:", e)
        return False
    finally:
        conn.close()

def delete_income(income_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM incomes WHERE id=?", (income_id,))
        conn.commit()
        return True
    except Exception as e:
        print("Delete income error:", e)
        return False
    finally:
        conn.close()

# ---------- Budget ----------
def get_monthly_budget(user_id: int) -> Optional[float]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT monthly_budget FROM budgets WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_budget(user_id: int, amount: float) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO budgets (user_id, monthly_budget) VALUES (?,?)", (user_id, float(amount)))
        conn.commit()
        return True
    except Exception as e:
        print("Set budget error:", e)
        return False
    finally:
        conn.close()

# ---------- Recurring ----------
def add_recurring_expense(category: str, amount: float, description: str, interval: str, user_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO recurring_expenses (category, amount, description, interval, user_id) VALUES (?,?,?,?,?)",
            (category, float(amount), description, interval, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print("Add recurring error:", e)
        return False
    finally:
        conn.close()

def fetch_recurring_expenses(user_id: int) -> List[Tuple]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, category, amount, description, interval FROM recurring_expenses WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_recurring_expense(rec_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM recurring_expenses WHERE id=?", (rec_id,))
        conn.commit()
        return True
    except Exception as e:
        print("Delete recurring error:", e)
        return False
    finally:
        conn.close()

# ---------- Backup / Restore ----------
def backup_db(dest_path: str) -> bool:
    try:
        shutil.copyfile(DB_NAME, dest_path)
        return True
    except Exception as e:
        print("Backup error:", e)
        return False

def restore_db(src_path: str) -> bool:
    try:
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        shutil.copyfile(src_path, DB_NAME)
        return True
    except Exception as e:
        print("Restore error:", e)
        return False
