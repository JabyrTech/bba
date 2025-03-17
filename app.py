from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os


from models import db, User, Course, Assignment, Submission, Enrollment, Note, SchoolNews, Attendance, Term, Timetable, Score

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    news = SchoolNews.query.all()

    scores = Score.query.filter_by(student_id=current_user.id).all()

    total_scores = 0
    count_courses = 0
    for s in scores:
        total_scores += s.total
        count_courses += 1
    overall_percentage = 0
    if count_courses > 0:
        overall_percentage = total_scores / count_courses

    sow = User.query.get(1)

    return render_template('home.html', user=current_user, news=news, sow = sow, current_class = get_current_class(user=current_user), overall_percentage = overall_percentage)
@app.route('/notes')
def noteapp():
    return render_template('note.html', user=current_user)

@app.route('/noteapp')
def notes():
    return render_template('notes.html', user=current_user)

@app.route('/calculator')
def calculator():
    return render_template('calculator.html', user=current_user)

@app.route('/sketch')
def sketch():
    return render_template('sketch.html', user=current_user)

@app.route('/translate')
def translate():
    return render_template('translate.html', user=current_user)

@app.route('/ptable')
def ptable():
    return render_template('ptable.html', user=current_user)

@app.route('/physics')
def physics():
    return render_template('physics.html', user=current_user)

@app.route('/dictionary')
def dictionary():
    return render_template('dictionary.html', user=current_user)

@app.route('/board')
def board():
    return render_template('board.html', user=current_user)

@app.route('/periodictable')
def periodictable():
    return render_template('periodictable.html', user=current_user)

# User Registration (without Flask-WTF)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role'].lower()
        lastname = request.form['lastname']
        othername = request.form['othername']
        designation = request.form['designaton']

        username = designation + " " + username

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(name=username, email=email, password=hashed_password, role=role, lastname=lastname, othername=othername)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('upload_image'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'danger')
            
    return render_template('login.html')

# User Dashboard
@app.route('/dashboard')
# @login_required
def dashboard():
    
    courses = Course.query.all()
    teachers = User.query.filter_by(role = 'teacher')
    
    return render_template('dashboard.html', user=current_user, courses=courses, teachers = teachers)

# View Course & Submit Assignment (without Flask-WTF)
@app.route('/courses')
def courses():
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_role = session.get('role')

    courses = Course.query.all()
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.student_id == user_id).all()

    teacher_courses = Course.query.filter_by(teacher_id = user_id)

    return render_template('course.html', courses=courses, role=user_role, enrolled_courses = enrolled_courses, teacher_courses=teacher_courses, user = current_user)



@app.route('/teacher/course/<int:course_id>/assignments')
@login_required
def assignments_page(course_id):
    # This route loads the single template 'assignments.html'
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    # If you want to show the create assignment form on the same page:
    course = Course.query.get(course_id)
    return render_template('assignments.html', assignments=assignments, course=course, user=current_user)


@app.route('/course/<int:course_id>/create_assignment', methods=['GET', 'POST'])
@login_required
def create_assignment(course_id):
    # Ensure current_user is teacher for that course
    # (Or you can do a role check: if current_user.role != 'teacher': return some error)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None

        new_assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            course_id=course_id
        )
        db.session.add(new_assignment)
        db.session.commit()
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('assignments_page', course_id=course_id))

    return redirect(url_for('assignments_page', course_id=course_id))


@app.route('/student/course/<int:course_id>/assignments')
@login_required
def student_assignments_page(course_id):
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    course = Course.query.get(course_id)
    return render_template('assignments.html', assignments=assignments, course=course, user=current_user)


@app.route('/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()

    student_answer = 'None'

    for i in submissions:
      if i.student.id == current_user.id:
        student_answer = i
    # Check if user is a student, or is enrolled in assignment.course_id

    if student_answer == 'None':
        if request.method == 'POST':
            content = request.form['content']
            new_submission = Submission(
                assignment_id=assignment_id,
                student_id=current_user.id,
                content=content,
                timestamp=datetime.now()
            )
            db.session.add(new_submission)
            db.session.commit()
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('courses_detail', course_id=assignment.course_id))
    else:
        if request.method == 'POST':
            student_answer.student_id = current_user.id
            student_answer.content = request.form['content']
            student_answer.timestamp = datetime.now()
            student_answer.assignment_id = assignment_id
            db.session.commit()
            flash('Assignment Edited Successfully!', 'success')

            return redirect(url_for('courses_detail', course_id=assignment.course_id))

    return render_template('assignments.html', assignment=assignment, user=current_user, student_answer = student_answer)


@app.route('/teacher/assignment/<int:assignment_id>/submissions')
@login_required
def view_all_submissions(assignment_id):

    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()

    return render_template('view_assignment.html', assignment=assignment, submission=submissions, user=current_user)

@app.route('/teacher/assignment/<int:assignment_id>/<int:student_id>')
@login_required
def view_submissions(assignment_id, student_id):
    student = User.query.get(student_id)

    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()

    student_answer = 'None'

    for i in submissions:
      if i.student.id == student.id:
        student_answer = i

    return render_template('grade.html', assignment=assignment, submission=submissions, user=current_user, student = student, student_answer=student_answer)

@app.route('/teacher/submission/<int:submission_id>/grade', methods=['POST'])
@login_required
def grade_submission(submission_id):
    # grading logic
    # then redirect back to the same grade.html
    submission = Submission.query.get_or_404(submission_id)
    assignment_id = submission.assignment_id
    # ... grading logic ...
    return redirect(url_for('view_submissions', assignment_id=assignment_id, user=current_user, submission = submission))


@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if user.role != 'student':
        flash('Only students can enroll in courses!', 'danger')
        return redirect(url_for('courses'))

    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(student_id=user_id, course_id=course_id).first()
    if existing_enrollment:
        flash('You are already enrolled in this course!', 'info')
        return redirect(url_for('courses'))

    # Enroll the student
    new_enrollment = Enrollment(student_id=user_id, course_id=course_id)
    db.session.add(new_enrollment)
    db.session.commit()
    flash('Successfully enrolled!', 'success')

    return redirect(url_for('courses'))

@app.route('/courses/<int:course_id>')
def courses_detail(course_id):
    course = Course.query.get(course_id)
    student = len(course.users)

    if course.color:
      color = course.color
    else:
      color = 'skyblue'

    if not course:
        abort(404)  # If course is not found, return 404 error
    return render_template('course_detail.html', course=course, user=current_user, students = student, color=color)


@app.route('/add-course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color')

        if not name or not description:
            flash("All fields are required!", "danger")
            return redirect(url_for('add_course'))

        # Creating the course with the current logged-in user as the teacher
        new_course = Course(
            name=name, 
            description=description,
            color=color, 
            teacher_id=current_user.id  # Assign the current user as the teacher
        )

        db.session.add(new_course)
        db.session.commit()
        flash("Course added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_course.html', user=current_user)


@app.route('/my_courses')
def my_courses():
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if user.role =='student':

        enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.student_id == user_id).all()

    else:

        enrolled_courses = Course.query.filter(Course.teacher_id == user_id).all()

    
    return render_template('my_courses.html', courses=enrolled_courses, user=current_user)


@app.route('/set_term', methods=['GET', 'POST'])
def set_term():
    if request.method == 'POST':
        start_date = request.form['start_date']
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = start_date + timedelta(weeks=11)
        
        new_term = Term(start_date=start_date, end_date=end_date)
        db.session.add(new_term)
        db.session.commit()
        
        flash('Term dates set successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('set_term.html', user=current_user)


@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    roles = ['teacher', 'admin']
    if 'user_id' not in session or session.get('role') not in roles:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    # Get today's date
    today = datetime.today().date()
    term = Term.query.order_by(Term.id.desc()).first()

    # Check if today is within the term dates
    if not (term.start_date <= today <= term.end_date):
        flash('Attendance can only be marked within the term dates!', 'warning')
        return redirect(url_for('dashboard'))

    # Get students
    students = User.query.filter_by(role='student').all()

    if request.method == 'POST':
        for student in students:
            status = request.form.get(f'status_{student.id}')
            if status:  # If a status is provided
                attendance = Attendance(date=today, status=status, student_id=student.id)
                db.session.add(attendance)

        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('mark_attendance'))

    return render_template('mark_attendance.html', students=students, today=today, user=current_user)


@app.route('/attendance_record/<int:student_id>')
def attendance_record(student_id):
    student = User.query.get_or_404(student_id)
    attendance_records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date).all()

    return render_template('attendance_record.html', student=student, attendance_records=attendance_records, user=current_user)



@app.route('/courses/<int:course_id>/scores', methods=['GET', 'POST'])
@login_required
def enter_scores(course_id):
    course = Course.query.get_or_404(course_id)
    # Ensure current_user is the teacher for this course

    # 1) Query all enrollments for this course
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()

    # 2) Extract the student objects from each enrollment
    students = [enroll.student for enroll in enrollments]


    if request.method == 'POST':
        # Loop through posted scores for each student
        for student_id in request.form.getlist('student_id'):
            test1 = float(request.form.get(f'test1_{student_id}', 0))
            test2 = float(request.form.get(f'test2_{student_id}', 0))
            exam = float(request.form.get(f'exam_{student_id}', 0))

            # Check if a score record exists
            score = Score.query.filter_by(student_id=student_id, course_id=course_id).first()
            if not score:
                score = Score(student_id=student_id, course_id=course_id)
                db.session.add(score)
            # Update the fields
            score.test1 = test1
            score.test2 = test2
            score.exam = exam
        db.session.commit()
        flash("Scores updated successfully!", "success")
        return redirect(url_for('enter_scores', course_id=course_id))

    # GET method: display table
    # For each student, load or create a Score object
    student_scores = []
    for s in students:
        score = Score.query.filter_by(student_id=s.id, course_id=course_id).first()
        if not score:
            score = Score(student_id=s.id, course_id=course_id, test1=0, test2=0, exam=0)
        student_scores.append((s, score))

    return render_template('teacher_score.html', course=course, student_scores=student_scores, user=current_user)





@app.route('/student/report_card')
@login_required
def student_report_card():
    # Ensure current_user is a student
    # Gather all scores for this student
    scores = Score.query.filter_by(student_id=current_user.id).all()
    # Summarize attendance
    # e.g. get from a StudentTerm or from user if stored in user
    days_present = 0
    days_absent = 0
    # Suppose we store attendance in StudentTerm for the current term
    # current_term = StudentTerm.query.filter_by(student_id=current_user.id, term_name="Term 1").first()
    # if current_term:
    #     days_present = current_term.days_present
    #     days_absent = current_term.days_absent

    # Calculate overall percentage across all courses
    # average of (score.total out of 100)
    total_scores = 0
    count_courses = 0
    for s in scores:
        total_scores += s.total
        count_courses += 1
    overall_percentage = 0
    if count_courses > 0:
        overall_percentage = total_scores / count_courses

    return render_template('report_card.html', scores=scores,
                           days_present=days_present, days_absent=days_absent,
                           overall_percentage=overall_percentage, user=current_user)


@app.route('/student/<int:student_id>')
def view_student_report(student_id):
    student = User.query.get_or_404(student_id)
    
    # Calculate overall percentage
    total_scores = sum(s.total for s in student.scores)
    total_courses = len(student.scores)
    overall_percentage = round(total_scores / total_courses, 2) if total_courses > 0 else 0

    return render_template('student_report.html', student=student, overall_percentage=overall_percentage, user=current_user)


@app.route('/profile/<int:id>')
def profile(id):
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(id)
    

    return render_template('profile.html', user=user, currentUser = current_user)

@app.route('/schoolbag', methods=['GET', 'POST'])
def school_bag():

    return render_template('schoolbag.html', user = current_user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # This removes designation from username (incase you forget)
    s = user.name
    ns = user.name
    if ' ' in s:
        d = s.index(' ')
        ns = s[d+1:]

    if request.method == 'POST':

        
        # Update common fields
        user.name = request.form['designation'] + " "  + request.form['name']
        

        if user.role == 'student':
            user.id_number = request.form['id_number']
            user.age = request.form['age']
            user.student_class = request.form['student_class']
            user.form = request.form['form']
            user.height = request.form['height']
            user.weight = request.form['weight']
            user.sport_house = request.form['sport_house']
            user.bio = request.form['bio']
            user.fav_subject = request.form['fav_subject']
            user.fav_color = request.form['fav_color']
            user.fav_food = request.form['fav_food']
            user.fav_sport = request.form['fav_sport']
            user.guardian_name = request.form['guardian_name']
            user.guardian_address = request.form['guardian_address']
            user.guardian_tel = request.form['guardian_tel']
            user.guardian_email = request.form['guardian_email']

        elif user.role == 'teacher':
            user.form = request.form['form']
            user.experience = request.form['experience']
            user.summary = request.form['summary']
            user.education = request.form['education']
            user.subject = request.form['subject']
            user.section = request.form['section']
            user.address = request.form['address']
            user.tel = request.form['tel']
            user.email = request.form['email']

            if request.form['subject'] == 'yes':
                user.is_classteacher = True
            else:
                user.is_classteacher = False

        # user.role = request.form['role']

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile/user.id'))

    return render_template('edit_profile.html', user=user, ns=ns)



@app.route('/view_users', methods=['GET', 'POST'])
def view_users():
    # Get unique forms for the filter dropdown
    forms = db.session.query(User.form).filter_by(role='student').distinct().all()
    forms = [f[0] for f in forms]  # Extract form names from tuples
    
    # Get selected form and search query from the request
    selected_form = request.args.get('form')
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)  # Pagination
    
    # Base query for students
    student_query = User.query.filter_by(role='student')

    student = 0

    for i in student_query:
      if i.role == 'student':
          student += 1
    
    # Apply form filter if selected
    if selected_form:
        student_query = student_query.filter_by(form=selected_form)
    
    # Apply search filter if provided
    if search_query:
        student_query = student_query.filter(User.name.ilike(f'%{search_query}%') | User.email.ilike(f'%{search_query}%'))
    
    # Sorting alphabetically and paginate the results (10 per page)
    students = student_query.order_by(User.name.asc()).paginate(page=page, per_page=10)
    
    # Get teachers sorted alphabetically (No filter for teachers)
    teachers = User.query.filter_by(role='teacher').order_by(User.name.asc()).all()
    
    return render_template('students.html', students=students, teachers=teachers, forms=forms, selected_form=selected_form, search_query=search_query, user=current_user, num = student)



@app.route('/view_teachers', methods=['GET', 'POST'])
def view_teachers():
    # Get unique forms for the filter dropdown
    
    subjects = db.session.query(User.subject).filter_by(role='teacher').distinct().all()
    subjects = [f[0] for f in subjects]  # Extract form names from tuples
    
    # Get selected form and search query from the request
    selected_subject = request.args.get('subject')
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)  # Pagination
    
    # Base query for teachers
    teacher_query = User.query.filter_by(role='teacher')
    
    # Apply form filter if selected
    if selected_subject:
        teacher_query = teacher_query.filter_by(subject=selected_subject)
    
    # Apply search filter if provided
    if search_query:
        teacher_query = teacher_query.filter(User.name.ilike(f'%{search_query}%') | User.email.ilike(f'%{search_query}%'))
    
    # Sorting alphabetically and paginate the results (10 per page)
    teachers = teacher_query.order_by(User.name.asc()).paginate(page=page, per_page=10)
    
    # Get teachers sorted alphabetically (No filter for teachers)
    # teachers = User.query.filter_by(role='teacher').order_by(User.name.asc()).all()
    
    return render_template('teachers.html', teachers=teachers, subjects=subjects, selected_subject=selected_subject, search_query=search_query, user=current_user)


# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))



@app.route('/lock-users', methods=['GET', 'POST'])
@login_required
def lock_users():
    
    user = current_user

    if current_user.role == 'student':
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('home'))
    else:

        search_query = request.args.get('search', '').strip()
        users = User.query.filter(User.name.ilike(f"%{search_query}%")).all() if search_query else []

        if request.method == 'POST':
            user_id = request.form.get('user_id')
            lock_status = request.form.get('lock_status') == 'yes'

            user = User.query.get(user_id)
            if user:
                user.is_locked = lock_status
                db.session.commit()
                flash(f"{user.name}'s lock status updated!", "success")
            else:
                flash("User not found!", "danger")

            return redirect(url_for('lock_users'))

    return render_template('lock_users.html', users=users,user=current_user)



@app.route('/rspw', methods=['GET', 'POST'])
def reset_password():

    search_query = request.args.get('search', '').strip()
    users = User.query.filter(User.name.ilike(f"%{search_query}%")).all() if search_query else []

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        reset = '00000000'

        user = User.query.get(user_id)
        if user:
            hashed_password = generate_password_hash(reset)
            user.password = hashed_password
            db.session.commit()
            flash(f"{user.name}'s password has been reset", "success")
        else:
            flash("User not found!", "danger")

        return redirect(url_for('reset_password'))

    return render_template('reset-password.html', users=users)




@app.route('/check_lock_status')
@login_required
def check_lock_status():
    return {"is_locked": current_user.is_locked}

@app.route('/notes', methods=['GET'])
@login_required
def get_notes():
    user_notes = Note.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'tags': note.tags.split(',') if note.tags else [],
        'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for note in user_notes])

@app.route('/notes', methods=['POST'])
@login_required
def create_note():
    data = request.get_json()
    new_note = Note(
        title=data['title'],
        content=data['content'],
        tags=','.join(data.get('tags', [])),
        user_id=current_user.id
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully'}), 201

@app.route('/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.tags = ','.join(data.get('tags', note.tags.split(',')))
    db.session.commit()
    return jsonify({'message': 'Note updated successfully'})

@app.route('/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_data = file.read()  # Read image binary data
            user = User.query.get(session['user_id'])  # Get logged-in user
            user.set_image(image_data)  # Convert & save as Base64
            db.session.commit()

            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('home'))

    return render_template('timetable.html')




# Admin Panel - Add/Edit Timetable
@app.route('/timetable', methods=['GET', 'POST'])
def add_timetable():
    if request.method == 'POST':
        form = request.form['form']
        time_start = request.form['time_start']
        time_end = request.form['time_end']
        day = request.form['day']
        subject = request.form['subject']

        new_entry = Timetable(form=form, time_start=time_start, time_end=time_end, day=day, subject=subject)
        db.session.add(new_entry)
        db.session.commit()
        flash('Timetable entry added successfully!', 'success')
        return redirect(url_for('add_timetable'))
    
    forms = db.session.query(User.form).filter_by(role='student').distinct().all()
    forms = [f[0] for f in forms]

    timetable_entries = Timetable.query.all()
    return render_template('admin_timetable.html', timetable_entries=timetable_entries, forms = forms, user = current_user)

# User View - Display Timetable
@app.route('/timetable/<form_name>')
def view_timetable(form_name):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    # Fetch and sort times in ascending order

    times = Timetable.query.filter_by(form=form_name).order_by(Timetable.time_start.asc()).all()

    timetable = Timetable.query.filter_by(form=form_name).all()

    # Organize timetable data for display
    timetable_data = {}
    for day in days:
        timetable_data[day] = {}
        for time in times:
            timetable_data[day][f"{time.time_start} - {time.time_end}"] = ''

    for entry in timetable:
        timetable_data[entry.day][f"{entry.time_start} - {entry.time_end}"] = entry.subject

    

    return render_template('view_timetable.html', timetable_data=timetable_data, times=times, days=days, form_name = form_name, user = current_user)





@app.route('/edit_subject/<form_name>', methods=['POST'])
def edit_subject(form_name):
    
    day = request.form['day']
    time = request.form['time']
    subject = request.form['subject']

    # Update the database
    timetable = Timetable.query.filter_by(form =form_name, day=day, time_start=time.split(' - ')[0], time_end=time.split(' - ')[1]).first()
    if timetable:
        timetable.subject = subject
    else:
        timetable = Timetable(form=form_name, day=day, time_start=time.split(' - ')[0], time_end=time.split(' - ')[1], subject=subject)
        db.session.add(timetable)

    db.session.commit()

    return redirect(url_for('view_timetable', form_name = form_name, user=current_user))



def get_current_class(user):
    # Get the current day and time
    current_day = datetime.now().strftime('%A')  # e.g., 'Monday'
    current_time = datetime.now().strftime('%H:%M')  # e.g., '10:30'

    # Get the user's form
    form_name = user.form

    # Query the timetable
    timetable = Timetable.query.filter_by(form=form_name, day=current_day).all()

    for entry in timetable:
        # Check if the current time is within the class time
        if entry.time_start <= current_time <= entry.time_end:
            return f"You have {entry.subject} from {entry.time_start} to {entry.time_end}."
    
    return "You have no class at this time."







# Delete Timetable Entry (Admin)
@app.route('/timetable/delete/<int:id>')
def delete_timetable(id):
    entry = Timetable.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Timetable entry deleted successfully!', 'success')
    return redirect(url_for('add_timetable'))

@app.route('/course/delete/<int:id>')
def deleteer(id):
    entry = Course.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Course entry deleted successfully!', 'success')
    
    return redirect(url_for('courses'))


from collections import defaultdict

def get_timetable():
    timetable_data = Timetable.query.order_by(Timetable.time_start).all()

    # Dictionary to store timetable where time is the key
    timetable = defaultdict(lambda: {"Monday": "", "Tuesday": "", "Wednesday": "", "Thursday": "", "Friday": ""})

    for entry in timetable_data:
        time_slot = f"{entry.time_start} - {entry.time_end}"
        timetable[time_slot][entry.day] = entry.subject

    return timetable


@app.route('/delete_time', methods=['POST'])
def delete_time():
    data = request.get_json()
    time_start = data.get('time_start')
    time_end = data.get('time_end')

    if time_start and time_end:
        Timetable.query.filter_by(time_start=time_start, time_end=time_end).delete()
        db.session.commit()
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": "Invalid time"}), 400


@app.route('/add-news', methods=['POST', 'GET'])
def add_news():

    if current_user.role != 'admin':
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        news = SchoolNews.query.get(1)
        news.title = request.form.get('title')
        news.description  = request.form.get('description')


        db.session.commit()
        flash("News Posted", "success")
        return redirect(url_for('home'))
    

    return render_template('add_news.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
