import tkinter as tk

from app.auth import ensure_default_admin
from app.database import init_db
from app.ui import LoginWindow, MainApp


def run_app() -> None:
    init_db()
    ensure_default_admin()

    root = tk.Tk()

    def open_main(user):
        for widget in root.winfo_children():
            widget.destroy()
        MainApp(root, user)

    LoginWindow(root, on_success=open_main)
    root.mainloop()


if __name__ == "__main__":
    run_app()
