import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from app import services
from app.auth import AuthUser


class LoginWindow:
    def __init__(self, root: tk.Tk, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("СКФУ Общежитие — Вход")
        self.root.geometry("380x190")

        frm = ttk.Frame(root, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Логин").grid(row=0, column=0, sticky="w")
        self.username = ttk.Entry(frm)
        self.username.grid(row=1, column=0, sticky="ew", pady=4)

        ttk.Label(frm, text="Пароль").grid(row=2, column=0, sticky="w")
        self.password = ttk.Entry(frm, show="*")
        self.password.grid(row=3, column=0, sticky="ew", pady=4)

        ttk.Button(frm, text="Войти", command=self.try_login).grid(row=4, column=0, pady=10, sticky="e")
        ttk.Label(frm, text="По умолчанию: admin / admin123", foreground="gray").grid(row=5, column=0, sticky="w")

        frm.columnconfigure(0, weight=1)

    def try_login(self):
        from app.auth import authenticate

        user = authenticate(self.username.get().strip(), self.password.get())
        if user is None:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            return
        self.on_success(user)


class MainApp:
    def __init__(self, root: tk.Tk, user: AuthUser):
        self.root = root
        self.user = user
        self.root.title(f"СКФУ Общежитие — {user.username} ({user.role})")
        self.root.geometry("1100x720")

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        if services.has_access(user.role, "students"):
            self.students_tab()
        if services.has_access(user.role, "rooms"):
            self.rooms_tab()
        if services.has_access(user.role, "stays"):
            self.stays_tab()
        if services.has_access(user.role, "finance"):
            self.finance_tab()
        if services.has_access(user.role, "reports"):
            self.reports_tab()

    def students_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Студенты")

        left = ttk.LabelFrame(tab, text="Добавить студента", padding=8)
        left.pack(side="left", fill="y")
        right = ttk.LabelFrame(tab, text="Список студентов", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=8)

        fields = ["full_name", "birth_date", "passport_data", "phone", "email", "study_group", "faculty", "study_mode", "notes"]
        labels = ["ФИО", "Дата рождения", "Паспорт", "Телефон", "Email", "Группа", "Факультет", "Форма обучения", "Примечание"]
        self.student_entries = {}
        for i, (field, label) in enumerate(zip(fields, labels)):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="w")
            e = ttk.Entry(left, width=30)
            e.grid(row=i, column=1, pady=2)
            self.student_entries[field] = e

        self.has_benefits = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="Есть льготы", variable=self.has_benefits).grid(row=len(fields), column=1, sticky="w")
        ttk.Button(left, text="Сохранить", command=self.save_student).grid(row=len(fields) + 1, column=1, sticky="e", pady=6)

        search_frame = ttk.Frame(right)
        search_frame.pack(fill="x")
        self.student_search = ttk.Entry(search_frame)
        self.student_search.pack(side="left", fill="x", expand=True)
        ttk.Button(search_frame, text="Поиск", command=self.refresh_students).pack(side="left", padx=4)

        cols = ("id", "full_name", "group", "faculty", "phone")
        self.students_tree = ttk.Treeview(right, columns=cols, show="headings")
        for col, title in zip(cols, ["ID", "ФИО", "Группа", "Факультет", "Телефон"]):
            self.students_tree.heading(col, text=title)
        self.students_tree.pack(fill="both", expand=True, pady=6)
        self.refresh_students()

    def save_student(self):
        data = {k: v.get().strip() for k, v in self.student_entries.items()}
        if not data["full_name"]:
            messagebox.showwarning("Проверка", "ФИО обязательно")
            return
        data["has_benefits"] = self.has_benefits.get()
        services.add_student(data)
        for v in self.student_entries.values():
            v.delete(0, tk.END)
        self.has_benefits.set(False)
        self.refresh_students()

    def refresh_students(self):
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)
        q = self.student_search.get().strip() if hasattr(self, "student_search") else ""
        for row in services.list_students(q):
            self.students_tree.insert("", tk.END, values=(row["id"], row["full_name"], row["study_group"], row["faculty"], row["phone"]))

    def rooms_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Комнаты")

        frm = ttk.LabelFrame(tab, text="Добавить комнату", padding=8)
        frm.pack(fill="x")
        self.building = ttk.Entry(frm, width=16)
        self.floor = ttk.Entry(frm, width=6)
        self.room_number = ttk.Entry(frm, width=10)
        self.total_beds = ttk.Entry(frm, width=8)
        self.status = ttk.Combobox(frm, values=["free", "partial", "full", "repair"], width=10)
        self.status.set("free")

        for i, (lbl, wid) in enumerate(
            [("Корпус", self.building), ("Этаж", self.floor), ("Комната", self.room_number), ("Мест", self.total_beds), ("Статус", self.status)]
        ):
            ttk.Label(frm, text=lbl).grid(row=0, column=i * 2, sticky="w")
            wid.grid(row=0, column=i * 2 + 1, padx=4)

        ttk.Button(frm, text="Сохранить", command=self.save_room).grid(row=0, column=10, padx=4)

        cols = ("id", "building", "floor", "room", "beds", "occupied", "status")
        self.rooms_tree = ttk.Treeview(tab, columns=cols, show="headings")
        headers = ["ID", "Корпус", "Этаж", "Комната", "Мест", "Занято", "Статус"]
        for c, h in zip(cols, headers):
            self.rooms_tree.heading(c, text=h)
        self.rooms_tree.pack(fill="both", expand=True, pady=8)
        self.refresh_rooms()

    def save_room(self):
        try:
            services.add_room(
                self.building.get().strip(),
                int(self.floor.get().strip()),
                self.room_number.get().strip(),
                int(self.total_beds.get().strip()),
                self.status.get().strip(),
            )
            self.refresh_rooms()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def refresh_rooms(self):
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
        for row in services.list_rooms():
            self.rooms_tree.insert(
                "",
                tk.END,
                values=(row["id"], row["building"], row["floor"], row["room_number"], row["total_beds"], row["occupied"], row["status"]),
            )

    def stays_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Заселение")

        top = ttk.LabelFrame(tab, text="Операции", padding=8)
        top.pack(fill="x")

        self.stay_student_id = ttk.Entry(top, width=10)
        self.stay_room_id = ttk.Entry(top, width=10)
        self.stay_date = ttk.Entry(top, width=12)
        self.stay_date.insert(0, date.today().isoformat())

        ttk.Label(top, text="ID студента").grid(row=0, column=0)
        self.stay_student_id.grid(row=0, column=1, padx=4)
        ttk.Label(top, text="ID комнаты").grid(row=0, column=2)
        self.stay_room_id.grid(row=0, column=3, padx=4)
        ttk.Label(top, text="Дата").grid(row=0, column=4)
        self.stay_date.grid(row=0, column=5, padx=4)
        ttk.Button(top, text="Заселить", command=self.perform_checkin).grid(row=0, column=6, padx=4)

        cols = ("id", "student", "building", "room", "checkin")
        self.stays_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for c, h in zip(cols, ["ID", "Студент", "Корпус", "Комната", "Дата заселения"]):
            self.stays_tree.heading(c, text=h)
        self.stays_tree.pack(fill="both", expand=True, pady=8)

        out = ttk.Frame(tab)
        out.pack(fill="x")
        self.checkout_reason = ttk.Entry(out)
        self.checkout_reason.pack(side="left", fill="x", expand=True)
        ttk.Button(out, text="Выселить выбранного", command=self.perform_checkout).pack(side="left", padx=4)

        self.refresh_stays()

    def perform_checkin(self):
        try:
            services.check_in(int(self.stay_student_id.get()), int(self.stay_room_id.get()), self.stay_date.get())
            self.refresh_stays()
            self.refresh_rooms()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def refresh_stays(self):
        for item in self.stays_tree.get_children():
            self.stays_tree.delete(item)
        for row in services.current_stays():
            self.stays_tree.insert("", tk.END, values=(row["id"], row["full_name"], row["building"], row["room_number"], row["checkin_date"]))

    def perform_checkout(self):
        selected = self.stays_tree.selection()
        if not selected:
            return
        stay_id = int(self.stays_tree.item(selected[0], "values")[0])
        services.check_out(stay_id, date.today().isoformat(), self.checkout_reason.get().strip())
        self.refresh_stays()
        self.refresh_rooms()

    def finance_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Оплаты")

        charge = ttk.LabelFrame(tab, text="Начисление", padding=8)
        charge.pack(fill="x")
        self.charge_student = ttk.Entry(charge, width=10)
        self.charge_period = ttk.Entry(charge, width=12)
        self.charge_amount = ttk.Entry(charge, width=10)
        self.charge_discount = ttk.Entry(charge, width=10)
        self.charge_period.insert(0, date.today().strftime("%Y-%m"))

        for i, (t, w) in enumerate(
            [("ID студента", self.charge_student), ("Период", self.charge_period), ("Сумма", self.charge_amount), ("Льгота", self.charge_discount)]
        ):
            ttk.Label(charge, text=t).grid(row=0, column=i * 2)
            w.grid(row=0, column=i * 2 + 1, padx=4)
        ttk.Button(charge, text="Начислить", command=self.save_charge).grid(row=0, column=8, padx=4)

        pay = ttk.LabelFrame(tab, text="Оплата", padding=8)
        pay.pack(fill="x", pady=6)
        self.pay_student = ttk.Entry(pay, width=10)
        self.pay_amount = ttk.Entry(pay, width=10)
        self.pay_method = ttk.Combobox(pay, values=["cash", "card", "transfer"], width=10)
        self.pay_method.set("transfer")

        for i, (t, w) in enumerate([("ID студента", self.pay_student), ("Сумма", self.pay_amount), ("Метод", self.pay_method)]):
            ttk.Label(pay, text=t).grid(row=0, column=i * 2)
            w.grid(row=0, column=i * 2 + 1, padx=4)
        ttk.Button(pay, text="Оплатить", command=self.save_payment).grid(row=0, column=6, padx=4)

    def save_charge(self):
        try:
            services.add_charge(
                int(self.charge_student.get()),
                self.charge_period.get().strip(),
                float(self.charge_amount.get()),
                float(self.charge_discount.get() or 0),
            )
            messagebox.showinfo("Готово", "Начисление добавлено")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def save_payment(self):
        try:
            services.add_payment(int(self.pay_student.get()), date.today().isoformat(), float(self.pay_amount.get()), self.pay_method.get())
            messagebox.showinfo("Готово", "Оплата зарегистрирована")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def reports_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Отчеты")

        ttk.Button(tab, text="Показать должников", command=self.show_debtors).pack(anchor="w")

        cols = ("student", "debt")
        self.report_tree = ttk.Treeview(tab, columns=cols, show="headings")
        self.report_tree.heading("student", text="Студент")
        self.report_tree.heading("debt", text="Задолженность")
        self.report_tree.pack(fill="both", expand=True, pady=8)

    def show_debtors(self):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for full_name, debt in services.debtors_report():
            self.report_tree.insert("", tk.END, values=(full_name, debt))
