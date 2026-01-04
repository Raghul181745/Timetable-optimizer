from flask import Flask, render_template, request, redirect, url_for, g, flash, session, make_response
import os
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = "secret123"

# Database setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "Timetable.db")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "timetable.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_name TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            semester TEXT NOT NULL,
            subject TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    # Attempt to add the 'year' column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE timetable ADD COLUMN year TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

# Time slots and days
time_slots = [
    "8:30 - 9:20",
    "9:20 - 10:10",
    "10:20 - 11:10",
    "11:10 - 12:00",
    "12:45 - 1:30",
    "1:30 - 2:20",
    "2:20 - 3:00"
]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Add entry route for manual timetable entry
@app.route("/add", methods=["GET", "POST"])
def add_entry():
    if request.method == "POST":
        staff_name = request.form["staff_name"]
        department = request.form["department"]
        year = request.form.get("year", "")
        semester = request.form["semester"]
        subject = request.form["subject"]
        day = request.form["day"]
        time = request.form["time"]
        db = get_db()
        conflict = db.execute(
            "SELECT * FROM timetable WHERE day=? AND time=?",
            (day, time)
        ).fetchone()
        if conflict:
            flash("⚠️ Slot already taken! Please choose another.")
            return redirect(url_for("add_entry"))
        db.execute(
            "INSERT INTO timetable (staff_name, department, year, semester, subject, day, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (staff_name, department, year, semester, subject, day, time)
        )
        db.commit()
        flash("✅ Entry added successfully!")
        return redirect(url_for("dashboard"))
    return render_template("add_timetable.html", days=days, time_slots=time_slots)

# Delete entry route
@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
    db.commit()
    flash("🗑️ Entry deleted successfully!")
    return redirect(url_for("dashboard"))

# Auto-assign slot route (from check_slots page)
@app.route("/auto_assign", methods=["POST"])
def auto_assign():
    staff_name = request.form.get("staff_name")
    department = request.form.get("department")
    year = request.form.get("year", "")
    semester = request.form.get("semester", "")
    subject = request.form.get("subject")
    db = get_db()
    used = db.execute(
        "SELECT day, time FROM timetable WHERE staff_name=? AND department=?",
        (staff_name, department)
    ).fetchall()
    used_slots = {(row["day"], row["time"]) for row in used}
    assigned = False
    for t in time_slots:
        for d in days:
            if (d, t) not in used_slots:
                db.execute(
                    "INSERT INTO timetable (staff_name, department, year, semester, subject, day, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (staff_name, department, year, semester, subject, d, t)
                )
                db.commit()
                flash(f"Auto-assigned {subject} to {d} {t}.")
                assigned = True
                break
        if assigned:
            break
    if not assigned:
        flash("No free slot available for auto-assign.")
    return redirect(url_for("check_slots"))

# Home route
@app.route("/")
def home():
    return redirect(url_for("dashboard"))

# Dashboard route
@app.route("/dashboard")
def dashboard():
    db = get_db()

    # Filter parameters
    staff_name = request.args.get("staff_name")
    department = request.args.get("department")
    year = request.args.get("year")

    query = "SELECT * FROM timetable WHERE 1=1"
    params = []

    if staff_name:
        query += " AND staff_name = ?"
        params.append(staff_name)
    if department:
        query += " AND department = ?"
        params.append(department)
    if year:
        query += " AND year = ?"
        params.append(year)

    entries = db.execute(query, params).fetchall()

    # Get distinct values for filter buttons
    departments = db.execute("SELECT DISTINCT department FROM timetable WHERE department != '' ORDER BY department").fetchall()
    years = db.execute("SELECT DISTINCT year FROM timetable WHERE year != '' ORDER BY year").fetchall()
    semesters = db.execute("SELECT DISTINCT semester FROM timetable WHERE semester != '' ORDER BY semester").fetchall()
    staff_list = db.execute("SELECT DISTINCT staff_name FROM timetable WHERE staff_name != '' ORDER BY staff_name").fetchall()

    # Logic for Grid View (Department Wise or Staff Wise)
    mode = request.args.get("mode")
    grid_view = False
    schedule = {d: {t: None for t in time_slots} for d in days}
    filter_desc = ""

    if mode == 'dept':
        dept = request.args.get("department")
        yr = request.args.get("year")
        sem = request.args.get("semester")
        if dept and yr and sem:
            grid_view = True
            filter_desc = f"Class Timetable: {dept} - Year {yr} - Semester {sem}"
            rows = db.execute("SELECT * FROM timetable WHERE department=? AND year=? AND semester=?", (dept, yr, sem)).fetchall()
            for row in rows:
                if row["day"] in schedule and row["time"] in schedule[row["day"]]:
                    schedule[row["day"]][row["time"]] = row

    elif mode == 'staff':
        staff = request.args.get("staff_name")
        if staff:
            grid_view = True
            filter_desc = f"Staff Timetable: {staff}"
            rows = db.execute("SELECT * FROM timetable WHERE staff_name=?", (staff,)).fetchall()
            for row in rows:
                if row["day"] in schedule and row["time"] in schedule[row["day"]]:
                    schedule[row["day"]][row["time"]] = row

    return render_template("dashboard.html", entries=entries, departments=departments, years=years, semesters=semesters, staff_list=staff_list, time_slots=time_slots, days=days, grid_view=grid_view, schedule=schedule, filter_desc=filter_desc, username=session.get("username", "Guest"))

# Export Excel Route
@app.route("/export_excel")
def export_excel():
    db = get_db()
    mode = request.args.get("mode")
    schedule = {d: {t: "" for t in time_slots} for d in days}
    filename = "timetable.csv"

    if mode == 'dept':
        dept = request.args.get("department")
        yr = request.args.get("year")
        sem = request.args.get("semester")
        if dept and yr and sem:
            filename = f"{dept}_{yr}_Sem{sem}_timetable.csv"
            rows = db.execute("SELECT * FROM timetable WHERE department=? AND year=? AND semester=?", (dept, yr, sem)).fetchall()
            for row in rows:
                if row["day"] in schedule and row["time"] in schedule[row["day"]]:
                    # Format: Subject (Staff Name)
                    schedule[row["day"]][row["time"]] = f"{row['subject']} ({row['staff_name']})"

    elif mode == 'staff':
        staff = request.args.get("staff_name")
        if staff:
            filename = f"{staff}_timetable.csv"
            rows = db.execute("SELECT * FROM timetable WHERE staff_name=?", (staff,)).fetchall()
            for row in rows:
                if row["day"] in schedule and row["time"] in schedule[row["day"]]:
                    # Format: Subject (Dept - Y:Year)
                    schedule[row["day"]][row["time"]] = f"{row['subject']} ({row['department']} - Y:{row['year']})"

    # Generate CSV
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Day"] + time_slots) # Header
    for d in days:
        row_data = [d] + [schedule[d][t] for t in time_slots]
        cw.writerow(row_data)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output

# Check slots route
@app.route("/check_slots", methods=["GET", "POST"])
def check_slots():
    slots = None
    staff_name = None
    department = None
    message = None
    if request.method == "POST":
        staff_name = request.form.get("staff_name")
        department = request.form.get("department")
        year = request.form.get("year", "")
        semester = request.form.get("semester", "")
        auto_assign = request.form.get("auto_assign")
        subject = request.form.get("subject")
        db = get_db()
        used = db.execute(
            "SELECT day, time, staff_name, subject, year, semester, id FROM timetable WHERE staff_name=? AND department=?",
            (staff_name, department)
        ).fetchall()
        used_slots = {(row["day"], row["time"]): row for row in used}
        # Auto-assign logic
        if auto_assign and subject:
            assigned = False
            for t in time_slots:
                for d in days:
                    if (d, t) not in used_slots:
                        db.execute(
                            "INSERT INTO timetable (staff_name, department, year, semester, subject, day, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (staff_name, department, year, semester, subject, d, t)
                        )
                        db.commit()
                        message = f"Auto-assigned {subject} to {d} {t}."
                        assigned = True
                        break
                if assigned:
                    break
            if not assigned:
                message = "No free slot available for auto-assign."
            # Refresh used_slots after auto-assign
            used = db.execute(
                "SELECT day, time, staff_name, subject, year, semester, id FROM timetable WHERE staff_name=? AND department=?",
                (staff_name, department)
            ).fetchall()
            used_slots = {(row["day"], row["time"]): row for row in used}
        # Build a grid: rows=time_slots, columns=days
        timetable_grid = []
        for t in time_slots:
            row = []
            for d in days:
                key = (d, t)
                if key in used_slots:
                    entry = used_slots[key]
                    # Display format: Subject (Y: 1 S: 2)
                    display_text = f"{entry['subject']} (Y:{entry['year']} S:{entry['semester']})"
                    row.append({"subject": display_text, "entry_id": entry['id']})
                else:
                    row.append({"subject": "Free", "entry_id": None})
            timetable_grid.append({"time": t, "slots": row})
        slots = timetable_grid
    return render_template("check_slots.html", slots=slots, staff_name=staff_name, department=department, days=days, message=message)

# Delete slot route (for check_slots page)
@app.route("/delete_slot/<int:entry_id>", methods=["POST"])
def delete_slot(entry_id):
    db = get_db()
    db.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
    db.commit()
    flash("🗑️ Slot deleted successfully!")
    return redirect(url_for("check_slots"))

# Login/logout routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Simple password check (You can change "admin" to whatever you want)
        if password == "admin":
            session["username"] = username
            flash("Logged in successfully!")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid password!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))

# Main
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
