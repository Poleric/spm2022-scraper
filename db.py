import sqlite3


class DB:
    def __init__(self, db_path: str):
        self.dbconn = sqlite3.connect(db_path)
        self.init_db()

    def init_db(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id TEXT PRIMARY KEY,
            subject_name TEXT
        );
        
        CREATE TABLE IF NOT EXISTS students (
            nokp TEXT PRIMARY KEY,
            angka_giliran TEXT UNIQUE,
            student_name TEXT,
            no_subjects INTEGER,
            passing INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS grades (
            grade_id INTEGER PRIMARY KEY,
            nokp INTEGER,
            subject_id INTEGER,
            grade TEXT,
            FOREIGN KEY(nokp) REFERENCES students(nokp),
            FOREIGN KEY(subject_id) REFERENCES subjects(subject_id)
        );
        """
        self.dbconn.executescript(schema)
        self.dbconn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dbconn.commit()
        self.close()

    def store_data(self, data: dict) -> None:
        angka_giliran = data["idx"]
        nokp = data["ic"].replace("-", "")
        student_name = data["cdd"]

        if data["certRem"] == "LAYAK MENDAPAT SIJIL":
            passing = True
        else:
            passing = False

        grades = data["subj"]
        no_subjects = len(grades)

        self.store_student(nokp, angka_giliran, student_name, no_subjects, passing)
        for grade in grades:
            self.store_subject(grade["c1"], grade["s1"])
            self.store_grade(nokp, grade["c1"], grade["g1"])

    def store_student(self, nokp: str, angka_giliran: str, student_name: str, no_subjects: int, passing: bool):
        stmt = """
        INSERT OR REPLACE INTO students (nokp, angka_giliran, student_name, no_subjects, passing) VALUES (?, ?, ?, ?, ?);
        """
        self.dbconn.execute(stmt, (nokp, angka_giliran, student_name, no_subjects, int(passing)))
        self.dbconn.commit()

    def store_subject(self, subject_id: str, subject_name: str) -> None:
        stmt = """
        INSERT OR IGNORE INTO subjects (subject_id, subject_name) VALUES (?, ?);
        """
        self.dbconn.execute(stmt, (subject_id, subject_name))

    def store_grade(self, nokp, subject_id, grade) -> None:
        if grade == "T":  # rename grade
            grade = "TH"

        stmt = """
        INSERT INTO grades (nokp, subject_id, grade) VALUES (?, ?, ?);
        """
        self.dbconn.execute(stmt, (nokp, subject_id, grade))

    def close(self) -> None:
        self.dbconn.close()

    def cursor(self) -> sqlite3.Cursor:
        return self.dbconn.cursor()


if __name__ == "__main__":
    with DB("./grades.db") as db:
        import scrape
        student_data = scrape.get_student_data("angka_giliran", "nokp")
        db.store_data(student_data)
    
