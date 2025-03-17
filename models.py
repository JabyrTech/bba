from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import base64

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=True)
    othername = db.Column(db.String(100), nullable=True)

    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # "student" or "teacher"
    is_locked = db.Column(db.Boolean, default=False)

    # Student-Specific Fields
    id_number = db.Column(db.String(50), unique=True, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    student_class = db.Column(db.String(50), nullable=True)
    form = db.Column(db.String(50), nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    sport_house = db.Column(db.String(50), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    fav_subject = db.Column(db.String(50), nullable=True)
    fav_color = db.Column(db.String(50), nullable=True)
    fav_food = db.Column(db.String(50), nullable=True)
    fav_sport = db.Column(db.String(50), nullable=True)

    # Parent/Guardian Information
    guardian_name = db.Column(db.String(100), nullable=True)
    guardian_address = db.Column(db.Text, nullable=True)
    guardian_tel = db.Column(db.String(20), nullable=True)
    guardian_email = db.Column(db.String(100), nullable=True)

    # Teacher-Specific Fields
    summary = db.Column(db.Text, nullable=True)
    tel = db.Column(db.String(100), nullable=True)
    subject = db.Column(db.String(200), nullable=True)
    education = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    section = db.Column(db.Text, nullable=True)
    is_classteacher = db.Column(db.Boolean, nullable=True)

    courses = db.relationship('Course', secondary='enrollment', back_populates='users')
    notes = db.relationship('Note', backref='user', lazy=True)

    profile_image = db.Column(db.Text, nullable=True)  # Store Base64 string
    news = db.relationship('SchoolNews', backref='user', lazy=True)

    def set_image(self, image_data):
        """Convert image binary data to Base64 and store it."""
        self.profile_image = base64.b64encode(image_data).decode('utf-8')

    def get_image(self):
        """Return Base64 string that can be used in an <img> tag."""
        return f"data:image/png;base64,{self.profile_image}" if self.profile_image else None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500), nullable=True)  # Store tags as comma-separated values
    created_at = db.Column(db.DateTime, )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    color = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    teacher = db.relationship('User', backref='user')
    users = db.relationship('User', secondary='enrollment', back_populates='courses')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    student = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course = db.relationship('Course', backref='assignments')

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)  # Could store text answers or a file path
    grade = db.Column(db.String(10), nullable=True)  # e.g. 'A', 'B', or numeric
    feedback = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)

    assignment = db.relationship('Assignment', backref='submissions')
    student = db.relationship('User', backref='submissions')


class SchoolNews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

# Attendance Record
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(1), nullable=False)  # 'P' for Present, 'A' for Absent
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student = db.relationship('User', backref=db.backref('attendance_records', lazy=True))

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form = db.Column(db.String(50), nullable=False)
    time_start = db.Column(db.String(10), nullable=False)
    time_end = db.Column(db.String(10), nullable=False)
    day = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Timetable {self.form} - {self.day} - {self.time_start} - {self.subject}>"

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    test1 = db.Column(db.Float, default=0.0)   # class test (20 marks)
    test2 = db.Column(db.Float, default=0.0)   # midterm test (20 marks)
    exam = db.Column(db.Float, default=0.0)    # final exam (60 marks)

    # Relationship backrefs
    student = db.relationship('User', backref='scores')
    course = db.relationship('Course', backref='scores')

    @property
    def total(self):
        """Calculate total out of 100."""
        return (self.test1 + self.test2 + self.exam)
