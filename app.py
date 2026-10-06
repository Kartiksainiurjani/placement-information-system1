import sqlite3
import streamlit as st

ADMIN_KEY = "admin123"  # change this


def run(q, p=(), fetch=False):
    con = sqlite3.connect("placement.db")
    con.row_factory = sqlite3.Row
    cur = con.execute(q, p)
    data = [dict(r) for r in cur.fetchall()] if fetch else None
    con.commit()
    con.close()
    return data


run("""CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, roll_no TEXT UNIQUE, email TEXT, cgpa REAL, skills TEXT)""")
run("""CREATE TABLE IF NOT EXISTS drives(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT, role TEXT, package TEXT, min_cgpa REAL, date TEXT)""")
run("""CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER, drive_id INTEGER, status TEXT DEFAULT 'Applied')""")

st.set_page_config(page_title="Placement Information System", page_icon="🎓")
st.title("🎓 Placement Information System")
page = st.sidebar.radio("Menu", ["Home", "Student Register", "Student Portal", "Admin"])

if page == "Home":
    total = run("SELECT COUNT(*) c FROM students", fetch=True)[0]["c"]
    placed = run("SELECT COUNT(DISTINCT student_id) c FROM applications "
                 "WHERE status='Selected'", fetch=True)[0]["c"]
    drives = run("SELECT * FROM drives", fetch=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Students", total)
    c2.metric("Drives", len(drives))
    c3.metric("Placed", placed)
    st.subheader("Upcoming drives")
    st.dataframe(drives)

elif page == "Student Register":
    with st.form("reg"):
        name = st.text_input("Name")
        roll = st.text_input("Roll No")
        email = st.text_input("Email")
        cgpa = st.number_input("CGPA", 0.0, 10.0, 6.0, 0.1)
        skills = st.text_input("Skills (comma separated)")
        if st.form_submit_button("Register"):
            try:
                run("INSERT INTO students(name,roll_no,email,cgpa,skills) "
                    "VALUES(?,?,?,?,?)", (name, roll, email, cgpa, skills))
                st.success("Registered successfully")
            except sqlite3.IntegrityError:
                st.error("Roll number already registered")

elif page == "Student Portal":
    roll = st.text_input("Enter your Roll No")
    if roll:
        stu = run("SELECT * FROM students WHERE roll_no=?", (roll,), True)
        if not stu:
            st.error("Student not found. Please register first.")
        else:
            stu = stu[0]
            st.write(f"Welcome, **{stu['name']}** (CGPA {stu['cgpa']})")
            drives = run("SELECT * FROM drives", fetch=True)
            st.subheader("Apply for a drive")
            if drives:
                options = {f"{d['company']} - {d['role']} (min CGPA {d['min_cgpa']})": d
                           for d in drives}
                choice = st.selectbox("Select drive", list(options))
                if st.button("Apply"):
                    d = options[choice]
                    dup = run("SELECT id FROM applications WHERE student_id=? "
                              "AND drive_id=?", (stu["id"], d["id"]), True)
                    if stu["cgpa"] < d["min_cgpa"]:
                        st.error("Your CGPA is below the minimum required")
                    elif dup:
                        st.error("Already applied")
                    else:
                        run("INSERT INTO applications(student_id,drive_id) VALUES(?,?)",
                            (stu["id"], d["id"]))
                        st.success("Applied successfully")
            else:
                st.info("No drives yet.")
            st.subheader("My applications")
            st.dataframe(run("""SELECT d.company, d.role, d.package, a.status
                FROM applications a JOIN drives d ON d.id=a.drive_id
                WHERE a.student_id=?""", (stu["id"],), True))

elif page == "Admin":
    key = st.text_input("Admin key", type="password")
    if key and key != ADMIN_KEY:
        st.error("Wrong admin key")
    elif key == ADMIN_KEY:
        tab1, tab2, tab3 = st.tabs(["Add Drive", "Applications", "Students"])
        with tab1:
            with st.form("drive"):
                company = st.text_input("Company")
                role = st.text_input("Role")
                package = st.text_input("Package (e.g. 4 LPA)")
                min_cgpa = st.number_input("Minimum CGPA", 0.0, 10.0, 6.0, 0.1)
                date = st.date_input("Drive date")
                if st.form_submit_button("Add drive"):
                    run("INSERT INTO drives(company,role,package,min_cgpa,date) "
                        "VALUES(?,?,?,?,?)", (company, role, package, min_cgpa, str(date)))
                    st.success("Drive added")
        with tab2:
            st.dataframe(run("""SELECT a.id, s.name, s.roll_no, d.company, a.status
                FROM applications a
                JOIN students s ON s.id=a.student_id
                JOIN drives d ON d.id=a.drive_id""", fetch=True))
            app_id = st.number_input("Application ID", 1, step=1)
            status = st.selectbox("New status",
                                  ["Applied", "Shortlisted", "Selected", "Rejected"])
            if st.button("Update status"):
                run("UPDATE applications SET status=? WHERE id=?", (status, int(app_id)))
                st.success("Status updated")
        with tab3:
            st.dataframe(run("SELECT * FROM students", fetch=True))
