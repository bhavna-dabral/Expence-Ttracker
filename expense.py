import flet as ft
from datetime import datetime
from collections import defaultdict

# Dummy credentials
USERS = {"admin": "password"}
expenses = []

def main(page: ft.Page):
    page.title = "💸 Expense Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS
    page.vertical_alignment = ft.MainAxisAlignment.START

    # === Login UI Elements ===
    username = ft.TextField(label="Username", width=300)
    password = ft.TextField(label="Password", password=True, width=300)
    login_msg = ft.Text(color=ft.Colors.RED)

    def do_login(e):
        if USERS.get(username.value) == password.value:
            show_app()
        else:
            login_msg.value = "❌ Invalid credentials"
            page.update()

    login_view = ft.Column(
        controls=[
            ft.Text("📥 Login", size=30, weight=ft.FontWeight.BOLD),
            username,
            password,
            ft.ElevatedButton("Login", on_click=do_login),
            login_msg
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # === Expense UI Elements ===
    amt = ft.TextField(label="Amount", width=200, keyboard_type=ft.KeyboardType.NUMBER)
    cat = ft.TextField(label="Category", width=200)
    dt = ft.TextField(label="Date (YYYY-MM-DD)", width=200)
    status = ft.Text(color=ft.Colors.RED)
    exp_list = ft.Column()
    pie = ft.PieChart()
    bar = ft.BarChart(
        left_axis=ft.ChartAxis(labels_size=30),
        bottom_axis=ft.ChartAxis(labels_size=30),
        expand=True,
    )

    def add_expense(_):
        try:
            date_str = dt.value.strip()
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")  # validate date
            amt_f = float(amt.value)

            # Add the expense
            expenses.append({
                "amount": amt_f,
                "category": cat.value.strip(),
                "date": date_str
            })

            # Clear inputs
            amt.value = ""
            cat.value = ""
            dt.value = ""
            status.value = ""

            refresh()
        except Exception as err:
            status.value = f"❌ Error: {err}"
        page.update()

    def refresh():
        exp_list.controls.clear()
        cat_totals = defaultdict(float)
        month_totals = [0.0] * 12

        for e in expenses:
            try:
                d = datetime.strptime(e["date"], "%Y-%m-%d")
                month_totals[d.month - 1] += e["amount"]
                cat_totals[e["category"]] += e["amount"]
                exp_list.controls.append(
                    ft.Text(f"{e['date']} | ₹{e['amount']:.2f} | {e['category']}")
                )
            except Exception:
                continue

        pie.sections = [
            ft.PieChartSection(value=v, title=f"{k} ₹{v:.2f}")
            for k, v in cat_totals.items()
        ]

        bar.bar_groups = [
            ft.BarChartGroup(
                x=i + 1,
                bar_rods=[ft.BarChartRod(to_y=amt, color=ft.Colors.BLUE)]
            )
            for i, amt in enumerate(month_totals) if amt > 0
        ]
        page.update()

    app_view = ft.Column(
        controls=[
            ft.Row([
                amt, cat, dt,
                ft.ElevatedButton("➕ Add", on_click=add_expense),
            ], spacing=10),
            status,
            ft.Divider(thickness=1),
            ft.Text("📋 Expense List", size=18, weight=ft.FontWeight.BOLD),
            exp_list,
            ft.Divider(thickness=1),
            ft.Text("📊 Category Distribution", size=18, weight=ft.FontWeight.BOLD),
            pie,
            ft.Divider(thickness=1),
            ft.Text("📅 Monthly Spend", size=18, weight=ft.FontWeight.BOLD),
            bar,
        ],
        spacing=10
    )

    def show_app():
        page.controls.clear()
        page.add(app_view)
        refresh()

    page.add(login_view)

ft.app(target=main)
