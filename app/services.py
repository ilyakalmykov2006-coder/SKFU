from app.database import get_connection


ROLE_PERMISSIONS = {
    "admin": {"students", "rooms", "stays", "finance", "reports", "admin"},
    "commandant": {"students", "rooms", "stays", "reports"},
    "accountant": {"finance", "reports"},
    "viewer": {"reports"},
}


def has_access(role: str, module: str) -> bool:
    return module in ROLE_PERMISSIONS.get(role, set())


def add_student(data: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO students (
            full_name, birth_date, passport_data, phone, email, study_group,
            faculty, study_mode, has_benefits, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["full_name"],
            data.get("birth_date"),
            data.get("passport_data"),
            data.get("phone"),
            data.get("email"),
            data.get("study_group"),
            data.get("faculty"),
            data.get("study_mode"),
            int(data.get("has_benefits", False)),
            data.get("notes"),
        ),
    )
    conn.commit()
    conn.close()


def list_students(query: str = "") -> list:
    conn = get_connection()
    if query:
        rows = conn.execute(
            """
            SELECT * FROM students
            WHERE full_name LIKE ? OR study_group LIKE ?
            ORDER BY full_name
            """,
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY full_name").fetchall()
    conn.close()
    return rows


def add_room(building: str, floor: int, room_number: str, total_beds: int, status: str = "free") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO rooms(building, floor, room_number, total_beds, status) VALUES (?, ?, ?, ?, ?)",
        (building, floor, room_number, total_beds, status),
    )
    conn.commit()
    conn.close()


def list_rooms() -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT r.*, (
            SELECT COUNT(*) FROM stays s WHERE s.room_id = r.id AND s.checkout_date IS NULL
        ) AS occupied
        FROM rooms r
        ORDER BY building, floor, room_number
        """
    ).fetchall()
    conn.close()
    return rows


def check_in(student_id: int, room_id: int, checkin_date: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO stays(student_id, room_id, checkin_date) VALUES (?, ?, ?)",
        (student_id, room_id, checkin_date),
    )
    conn.commit()
    conn.close()


def check_out(stay_id: int, checkout_date: str, reason: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE stays SET checkout_date=?, checkout_reason=? WHERE id=?",
        (checkout_date, reason, stay_id),
    )
    conn.commit()
    conn.close()


def current_stays() -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id, st.full_name, r.building, r.room_number, s.checkin_date
        FROM stays s
        JOIN students st ON st.id=s.student_id
        JOIN rooms r ON r.id=s.room_id
        WHERE s.checkout_date IS NULL
        ORDER BY s.checkin_date DESC
        """
    ).fetchall()
    conn.close()
    return rows


def add_charge(student_id: int, period: str, amount: float, benefit_discount: float = 0) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO charges(student_id, period, amount, benefit_discount) VALUES (?, ?, ?, ?)",
        (student_id, period, amount, benefit_discount),
    )
    conn.commit()
    conn.close()


def add_payment(student_id: int, payment_date: str, amount: float, method: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO payments(student_id, payment_date, amount, method) VALUES (?, ?, ?, ?)",
        (student_id, payment_date, amount, method),
    )
    conn.commit()
    conn.close()


def debtors_report() -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT st.id, st.full_name,
               COALESCE((SELECT SUM(c.amount - c.benefit_discount) FROM charges c WHERE c.student_id=st.id), 0) AS total_charges,
               COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.student_id=st.id), 0) AS total_payments
        FROM students st
        ORDER BY st.full_name
        """
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        debt = float(row["total_charges"] or 0) - float(row["total_payments"] or 0)
        if debt > 0:
            result.append((row["full_name"], round(debt, 2)))
    return result
