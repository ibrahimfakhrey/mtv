import json
import os
from datetime import datetime

from flask_mail import Mail, Message
from flask import Flask, render_template, redirect, url_for, flash, abort, request, jsonify,send_from_directory, session

from werkzeug.security import generate_password_hash, check_password_hash

from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.utils import secure_filename
import pandas as pd
from flask_babel import Babel
import fitz  # PyMuPDF
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

babel = Babel(app)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '3omarislam911@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-me')

# Tell browsers (and any CDN) to cache static files for 30 days.
# Image/CSS/JS URLs in this app don't change, so this is safe.
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60 * 60 * 24 * 30  # 30 days

# Database URI: use DATABASE_URL env var if set (Railway), otherwise default to
# the local instance/users.db that Flask-SQLAlchemy creates by default.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///users.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

# Upload folder: use UPLOAD_FOLDER env var if set (Railway volume path),
# otherwise fall back to static/uploads next to this file.
UPLOAD_FOLDER = os.environ.get(
    'UPLOAD_FOLDER', os.path.join(BASE_DIR, 'static', 'uploads')
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Admin credentials (read from env in production)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Meerim')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Mvt@meerimuae')


with app.app_context():
    class Course(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        training_program = db.Column(db.String(1000))
        duration_days = db.Column(db.String(1000))
        available = db.Column(db.String(1000))
        language = db.Column(db.String(1000))
        start_date = db.Column(db.String(1000))
        end_date = db.Column(db.String(1000))
        where = db.Column(db.String(1000))

    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(1000))
        last_name = db.Column(db.String(1000))
        email = db.Column(db.String(1000))
        contact_number = db.Column(db.String(1000))
        company_name = db.Column(db.String(1000))
        training_program = db.Column(db.String(1000))

    class Register(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        first_n = db.Column(db.String(1000))
        last_n = db.Column(db.String(1000))
        username = db.Column(db.String(1000))
        password = db.Column(db.String(1000))

    class Register1(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        first_n = db.Column(db.String(1000))
        last_n = db.Column(db.String(1000))
        username = db.Column(db.String(1000))
        password = db.Column(db.String(1000))

        def set_password(self, password):
            self.password = generate_password_hash(password, method='pbkdf2:sha256')

        def check_password(self, password):
            return check_password_hash(self.password, password)


    class UploadedFile(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        filename = db.Column(db.String(255), nullable=False)
        filetype = db.Column(db.String(50))
        upload_time = db.Column(db.DateTime, default=datetime.utcnow)


    class UploadedFile1(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        filename = db.Column(db.String(255), nullable=False)
        filetype = db.Column(db.String(50))
        cover_image_filename = db.Column(db.String(255), nullable=False)  # New column for cover image
        upload_time = db.Column(db.DateTime, default=datetime.utcnow)


    class Test(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(150))
        test_type = db.Column(db.String(50))  # 'multiple_choice', 'true_false', 'written'
        time_limit = db.Column(db.Integer)  # in minutes
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        # Link to questions with cascade delete
        questions = db.relationship('Question', backref='test', cascade="all, delete-orphan")
        # Add this line to cascade delete StudentAnswer records
        student_answers = db.relationship('StudentAnswer', backref='test', cascade="all, delete-orphan")


    class Question(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
        question_text = db.Column(db.String(500), nullable=False)

        # Optional fields for MCQ
        choice1 = db.Column(db.String(200))
        choice2 = db.Column(db.String(200))
        choice3 = db.Column(db.String(200))
        choice4 = db.Column(db.String(200))
        correct_answer = db.Column(db.String(500))

        answers = db.relationship('StudentAnswer', backref='question', cascade="all, delete-orphan")

    class StudentAnswer(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey('register1.id'))
        test_id = db.Column(db.Integer, db.ForeignKey('test.id'))
        question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
        answer = db.Column(db.Text)
        submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
        grade = db.Column(db.Float, nullable=True)


    class CourseContent(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey('register1.id'), nullable=False)
        filename = db.Column(db.String(255), nullable=False)
        filetype = db.Column(db.String(50))
        upload_time = db.Column(db.DateTime, default=datetime.utcnow)

        student = db.relationship('Register1', backref=db.backref('course_contents', lazy=True))


    class Certificate(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey('register1.id'), nullable=False)
        filename = db.Column(db.String(255), nullable=False)
        filetype = db.Column(db.String(50))
        upload_time = db.Column(db.DateTime, default=datetime.utcnow)

        student = db.relationship('Register1', backref=db.backref('certificates', lazy=True))


    db.create_all()

    class MyModelView(ModelView):
        def is_accessible(self):
            return False

admin = Admin(app)
admin.add_view(MyModelView(Course, db.session))
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Register, db.session))
admin.add_view(MyModelView(Register1, db.session))
admin.add_view(MyModelView(UploadedFile, db.session))
admin.add_view(MyModelView(UploadedFile1, db.session))
admin.add_view(MyModelView(Test, db.session))
admin.add_view(MyModelView(Question, db.session))
admin.add_view(MyModelView(StudentAnswer, db.session))
admin.add_view(MyModelView(CourseContent, db.session))
admin.add_view(MyModelView(Certificate, db.session))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Register1.query.get(int(user_id))


# Serve uploaded files from the configured UPLOAD_FOLDER. On Railway this
# is the persistent volume (/data/uploads); locally it's static/uploads.
# This route overrides Flask's default /static/uploads/* handler.
@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ────────────────────────────────────────────────────────────────────────────
# TEMPORARY: one-time data seed route. Remove after seeding the Railway volume.
# Requires the SEED_TOKEN env var to be set; otherwise returns 404.
# ────────────────────────────────────────────────────────────────────────────
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # allow 200 MB uploads for seeding

@app.route('/_seed', methods=['GET', 'POST'])
def seed_data():
    expected = os.environ.get('SEED_TOKEN')
    if not expected:
        abort(404)
    token = request.values.get('token')
    if token != expected:
        abort(403)

    upload_dir = app.config['UPLOAD_FOLDER']
    data_root = os.path.dirname(upload_dir.rstrip('/')) or '/data'
    db_path = os.path.join(data_root, 'users.db')

    if request.method == 'GET':
        return f'''<!doctype html><meta charset=utf-8>
<title>Seed</title>
<style>body{{font-family:system-ui;max-width:560px;margin:40px auto;padding:0 16px}}code{{background:#eee;padding:2px 6px;border-radius:4px}}</style>
<h1>One-time data seed</h1>
<p>Data root: <code>{data_root}</code></p>
<p>DB target: <code>{db_path}</code></p>
<p>Uploads target: <code>{upload_dir}</code></p>
<form method=post enctype=multipart/form-data>
  <input type=hidden name=token value="{token}">
  <p><label>users.db file:<br><input type=file name=users_db></label></p>
  <p><label>uploads.zip file:<br><input type=file name=uploads_zip></label></p>
  <p><button type=submit>Upload</button></p>
</form>'''

    log = []

    f = request.files.get('users_db')
    if f and f.filename:
        os.makedirs(data_root, exist_ok=True)
        f.save(db_path)
        log.append(f'wrote {db_path} ({os.path.getsize(db_path)} bytes)')
        db.engine.dispose()
        log.append('disposed sqlalchemy engine (new queries will read the new DB)')

    f = request.files.get('uploads_zip')
    if f and f.filename:
        import zipfile, tempfile
        os.makedirs(upload_dir, exist_ok=True)
        tmp_path = tempfile.mktemp(suffix='.zip')
        f.save(tmp_path)
        try:
            with zipfile.ZipFile(tmp_path) as zf:
                extracted = 0
                for member in zf.namelist():
                    if member.endswith('/'):
                        continue
                    name = os.path.basename(member)
                    if not name or name.startswith('.') or '__MACOSX' in member:
                        continue
                    with zf.open(member) as src, open(os.path.join(upload_dir, name), 'wb') as dst:
                        dst.write(src.read())
                    extracted += 1
            log.append(f'extracted {extracted} files into {upload_dir}')
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    log.append('done')
    return '<pre>' + '\n'.join(log) + '</pre>'
# ────────────────────────────────────────────────────────────────────────────

@app.route("/")
def main():
    # Get all uploaded files with their cover images
    files = UploadedFile1.query.all()
    return render_template("index.html", files=files)

# For SQLite foreign key support
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):  # play safe
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()




@app.route("/consulting")
def consulting():
    return render_template("consulting.html")

@app.route("/2025_Training_Plan")
def exel():
    return render_template("display_exel.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/elements")
def elements():
    return render_template("elements.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_n = request.form['first_n']
        last_n = request.form['last_n']
        username = request.form['username']
        password = request.form['password']

        existing_user = Register1.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Try another one.', 'error')
            return redirect(url_for('register'))

        new_user = Register1(first_n=first_n, last_n=last_n, username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Register1.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')

            # Check if this is the admin user
            if user.username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                return redirect(url_for('admin_dashboard'))  # Your admin page route
            else:
                return redirect(request.args.get('next') or url_for('student_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    file = request.files['file']

    if file and allowed_file(file.filename):
        file_filename = secure_filename(file.filename)
        file_ext = file_filename.rsplit('.', 1)[1].lower()
        file_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_filename)
        file.save(file_filepath)

        # Default cover image (if not a PDF)
        cover_image_filename = 'default_thumbnail.png'

        if file_ext == 'pdf':
            try:
                doc = fitz.open(file_filepath)
                page = doc.load_page(0)
                pix = page.get_pixmap()
                cover_image_filename = file_filename.rsplit('.', 1)[0] + '.png'
                cover_image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], cover_image_filename)
                pix.save(cover_image_filepath)
                doc.close()
            except Exception as e:
                flash(f'Error generating PDF thumbnail: {e}', 'warning')

        # Save to database
        new_file = UploadedFile1(
            filename=file_filename,
            filetype=file.content_type,
            cover_image_filename=cover_image_filename
        )
        db.session.add(new_file)
        db.session.commit()

        flash('File uploaded successfully!', 'success')
    else:
        flash('Unsupported file type.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route("/delete_file/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):

    file = UploadedFile1.query.get_or_404(file_id)

    # Paths
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.cover_image_filename)

    try:
        # Delete main file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete cover image
        if os.path.exists(cover_image_path):
            os.remove(cover_image_path)

        # Delete from database
        db.session.delete(file)
        db.session.commit()

        flash('File and cover image deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))





@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    users = Register1.query.all()
    uploaded_files = UploadedFile1.query.all()
    tests = Test.query.all()
    course_contents = CourseContent.query.all()
    certificates = Certificate.query.all()
    return render_template('admin_dashboard.html', users=users, uploaded_files=uploaded_files, tests=tests, course_contents=course_contents, certificates=certificates)


@app.route('/create_test', methods=['POST'])
def create_test():
    test_title = request.form['title']
    test_type = request.form['test_type']
    time_limit = request.form['time_limit']

    # Create and save the new test
    new_test = Test(
        title=test_title,
        test_type=test_type,
        time_limit=time_limit
    )
    db.session.add(new_test)
    db.session.commit()

    # Now loop through dynamic questions
    question_num = 1
    while True:
        question_key = f'question_{question_num}'
        correct_key = f'correct_{question_num}'

        if question_key not in request.form:
            break  # No more questions

        question_text = request.form[question_key]
        correct_answer = request.form.get(correct_key, '')

        # Default choices to None
        choice1 = choice2 = choice3 = choice4 = None

        if test_type == 'multiple_choice':
            choice1 = request.form.get(f'choice_{question_num}_1')
            choice2 = request.form.get(f'choice_{question_num}_2')
            choice3 = request.form.get(f'choice_{question_num}_3')
            choice4 = request.form.get(f'choice_{question_num}_4')

        # Create a question object
        new_question = Question(
            test_id=new_test.id,
            question_text=question_text,
            choice1=choice1,
            choice2=choice2,
            choice3=choice3,
            choice4=choice4,
            correct_answer=correct_answer
        )
        db.session.add(new_question)
        question_num += 1

    db.session.commit()
    return redirect('/admin_dashboard')



@app.route('/submit_test', methods=['POST'])
def submit_test():
    test_id = request.form.get('test_id')
    student_id = session.get('student_id')  # Retrieve student ID from the session

    # Get all related questions for the test
    questions = Question.query.filter_by(test_id=test_id).all()

    for q in questions:
        answer = request.form.get(f'answer_{q.id}')
        if answer:
            student_answer = StudentAnswer(
                student_id=student_id,  # Use student_id instead of student_name
                test_id=test_id,
                question_id=q.id,
                answer=answer
            )
            db.session.add(student_answer)

    db.session.commit()
    return "Test submitted successfully!"

@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    db.session.delete(test)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    student_id = session.get('student_id')

    # Get test IDs that student answered AND still exist
    answered_test_ids = db.session.query(StudentAnswer.test_id).filter_by(student_id=student_id).distinct()
    answered_test_ids = [tid for (tid,) in answered_test_ids if Test.query.get(tid)]

    available_tests = Test.query.all()

    course_contents = CourseContent.query.filter_by(student_id=current_user.id).all()
    certificates = Certificate.query.filter_by(student_id=current_user.id).all()

    return render_template(
        'student_dashboard.html',
        tests=available_tests,
        completed_test_ids=answered_test_ids,
        course_contents=course_contents,
        certificates=certificates
    )

@app.route("/delete_student_file/<int:file_id>/<category>", methods=["POST"])
@login_required
def delete_student_file(file_id, category):
    if category == "course_content":
        file = CourseContent.query.get_or_404(file_id)
    elif category == "certificate":
        file = Certificate.query.get_or_404(file_id)
    else:
        flash("Invalid category", "error")
        return redirect(url_for("admin_dashboard"))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(file)
    db.session.commit()

    flash("Student file deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))




@app.route('/take_test/<int:test_id>', methods=['GET', 'POST'])
def take_test(test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()

    # ✅ Get student_id from session (must be set during login)
    student_id = session.get('student_id')

    if request.method == 'POST':
        for q in questions:
            ans = request.form.get(f'question_{q.id}')
            if ans:  # Make sure the student actually answered
                student_answer = StudentAnswer(
                    student_id=student_id,
                    test_id=test.id,
                    question_id=q.id,
                    answer=ans
                )
                db.session.add(student_answer)
        db.session.commit()
        return redirect('/student_dashboard')

    return render_template('take_test.html', test=test, questions=questions)



@app.route('/view_submissions/<int:test_id>')
def view_submissions(test_id):
    answers = StudentAnswer.query.filter_by(test_id=test_id).all()
    return render_template('view_submissions.html', answers=answers)

@app.route('/view_result/<int:test_id>')
def view_result(test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()
    student_id = session.get('student_id')
    student_answers = StudentAnswer.query.filter_by(test_id=test_id, student_id=student_id).all()

    student_answers_dict = {answer.question_id: answer.answer for answer in student_answers}

    result = []
    correct_count = 0

    for question in questions:
        student_answer = student_answers_dict.get(question.id)
        correct_answer = question.correct_answer
        is_correct = student_answer == correct_answer
        if is_correct:
            correct_count += 1
        result.append({
            'question': question.question_text,
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })

    score = round((correct_count / len(questions)) * 100, 2)  # Score in percentage

    return render_template('view_result.html', test=test, result=result, score=score)

@app.route('/upload_student_file', methods=['POST'])
@login_required
def upload_student_file():
    student_id = request.form['student_id']
    file_category = request.form['file_category']
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if file_category == 'course_content':
            new_file = CourseContent(
                student_id=student_id,
                filename=filename,
                filetype=file.content_type
            )
        elif file_category == 'certificate':
            new_file = Certificate(
                student_id=student_id,
                filename=filename,
                filetype=file.content_type
            )
        else:
            flash('Invalid file category.', 'error')
            return redirect(url_for('admin_dashboard'))

        db.session.add(new_file)
        db.session.commit()
        flash(f'{file_category.replace("_", " ").title()} uploaded successfully!', 'success')
    else:
        flash('Unsupported file type.', 'error')

    return redirect(url_for('admin_dashboard'))





@app.route("/apply", methods=["GET","POST"])
def apply():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        contact_number = request.form.get("contact_number")
        company_name = request.form.get("company_name")
        training_program = request.form.get("training_program")

        users = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            contact_number=contact_number,
            company_name=company_name,
            training_program=training_program
        )
        db.session.add(users)
        db.session.commit()
        try:
            msg = Message('Hello from Meerim Visionary Training', sender='3omarislam911@gmail.com',
                          recipients=['info@mvtuae.com'])
            msg.body = f'Dear Meerim Visionary Training,\n\n' \
                       f'I hope this email finds you well.\n\n' \
                       f'Full Name: {first_name} {last_name}\n' \
                       f'Email Address: {email}\n' \
                       f'Contact Number: {contact_number}\n' \
                       f'Company Name: {company_name}\n' \
                       f'Training Program: {training_program}\n'

            mail.send(msg)
            return render_template("email_sent.html")
        except Exception as e:
            return f"An Error Occurred: {e}"
    return render_template("apply.html")



@app.route('/ssss')
def process_excel_sss():

    try:
        # ------------------------------------------------------------------
        # Resolve absolute path safely (same directory as this file)
        # ------------------------------------------------------------------
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_name = '2026 -Training Plan - MVT.xlsx'
        file_path = os.path.join(BASE_DIR, file_name)

        # Debug logs (VERY IMPORTANT – do not remove until confirmed working)
        app.logger.info(f"Current working directory: {os.getcwd()}")
        app.logger.info(f"Base directory (__file__): {BASE_DIR}")
        app.logger.info(f"Looking for Excel file at: {file_path}")
        app.logger.info(f"Files in BASE_DIR: {os.listdir(BASE_DIR)}")

        # ------------------------------------------------------------------
        # Ensure file exists
        # ------------------------------------------------------------------
        if not os.path.exists(file_path):
            return jsonify({
                "error": "Excel file not found",
                "expected_path": file_path,
                "files_found": os.listdir(BASE_DIR)
            }), 404

        # ------------------------------------------------------------------
        # Read Excel (all sheets)
        # ------------------------------------------------------------------
        excel_data = pd.read_excel(
            file_path,
            sheet_name=None,
            skiprows=1
        )

        rows_added = 0

        # ------------------------------------------------------------------
        # Process sheets
        # ------------------------------------------------------------------
        for sheet_name, df in excel_data.items():
            app.logger.info(f"Processing sheet: {sheet_name}")

            if df.empty:
                app.logger.warning(f"Sheet '{sheet_name}' is empty, skipping.")
                continue

            # Drop first column
            df = df.iloc[:, 1:]

            if df.shape[1] < 7:
                app.logger.warning(
                    f"Sheet '{sheet_name}' has insufficient columns, skipping."
                )
                continue

            for index, row in df.iterrows():

                # Skip empty rows
                if row.isna().all():
                    continue

                # Required field
                if pd.isna(row.iloc[0]):
                    continue

                training_program = str(row.iloc[0]).strip()
                duration_days = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
                available = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
                language = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None

                # Safe date parsing
                try:
                    start_date = (
                        pd.to_datetime(row.iloc[4]).date()
                        if pd.notna(row.iloc[4]) else None
                    )
                    end_date = (
                        pd.to_datetime(row.iloc[5]).date()
                        if pd.notna(row.iloc[5]) else None
                    )
                except Exception as e:
                    app.logger.warning(
                        f"Row {index} in sheet '{sheet_name}' skipped due to date error: {e}"
                    )
                    continue

                where = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else None

                # Insert into DB
                db.session.add(
                    Course(
                        training_program=training_program,
                        duration_days=duration_days,
                        available=available,
                        language=language,
                        start_date=start_date,
                        end_date=end_date,
                        where=where
                    )
                )

                rows_added += 1

        # ------------------------------------------------------------------
        # Commit once
        # ------------------------------------------------------------------
        db.session.commit()

        return jsonify({
            "message": "Excel imported successfully",
            "rows_added": rows_added
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Fatal error: {e}")
        return jsonify({
            "error": "Failed to process Excel file",
            "details": str(e)
        }), 500



@app.route("/2025_Training_Plan/1")
def training1():
    courses=Course.query.all()
    name="Electrical & Power Engineering & Renewable Energy"
    cc=[]
    for i in range(0,140):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/2")
def training2():
    courses=Course.query.all()
    name="MECHANICAL ENGINEERING & MAINTENANCE"
    cc=[]
    for i in range(140,240):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/3")
def training3():
    courses=Course.query.all()
    name="INSTRUMENTATION & CONTROL ENGINEERING"
    cc=[]
    for i in range(240,340):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/4")
def training4():
    courses=Course.query.all()
    name="Oil & Gas (Drilling, Reservoir, Petroleum & Geology)"
    cc=[]
    for i in range(340,440):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/5")
def training5():
    courses=Course.query.all()
    name="Cement Manufacturing"
    cc=[]
    for i in range(440,540):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/6")
def training6():
    courses=Course.query.all()
    name="Iron and Steel Manufacturing"
    cc=[]
    for i in range(540,590):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/7")
def training7():
    courses=Course.query.all()
    name="Aluminium Manufacturing"
    cc=[]
    for i in range(590,640):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/8")
def training8():
    courses=Course.query.all()
    name="Water & Waste Water Treatment and Chemistry Engineering"
    cc=[]
    for i in range(640,840):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/9")
def training9():
    courses=Course.query.all()
    name="Information Technology (IT)"
    cc=[]
    for i in range(840,940):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/10")
def training10():
    courses=Course.query.all()
    name="Health & Safety Management"
    cc=[]
    for i in range(940,1040):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/11")
def training11():
    courses=Course.query.all()
    name="Procurement & Supply Chain Management"
    cc=[]
    for i in range(1040,1140):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/12")
def training12():
    courses=Course.query.all()
    name="Marine & Offshore Engineering"
    cc=[]
    for i in range(1140,1240):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/13")
def training13():
    courses=Course.query.all()
    name="Project & Contract Management"
    cc=[]
    for i in range(1240,1340):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/14")
def training14():
    courses=Course.query.all()
    name="HRM & Strategic Management C-Level Programs"
    cc=[]
    for i in range(1340,1440):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route("/2025_Training_Plan/15")
def training15():
    courses=Course.query.all()
    name="Finance, Banking & Budgeting Management"
    cc=[]
    for i in range(1440,1540):
        cc.append(courses[i])
    return render_template("display_exel.html",courses=cc,name=name)

@app.route('/upcoming_events')
def upcoming_events():
    # Simulate the current datetime as January 2025 for this example
    current_datetime = datetime.strptime("2026-06-01", "%Y-%m-%d")


    # Extract the year and month for comparison
    year = current_datetime.year
    month = current_datetime.month

    # Format the date as "YYYY-MM"
    formatted_date_today = f'{year:04d}-{month:02d}'

    all_courses = Course.query.all()
    upcoming_courses = []

    for course in all_courses:
        due_month = course.start_date
        course_date = due_month.split()[0]  # Get the "YYYY-MM-DD" part
        course_year_month = '-'.join(course_date.split('-')[:2])  # Get the "YYYY-MM"

        if formatted_date_today == course_year_month:
            upcoming_courses.append(course)

    return render_template('upcomming.html', all_courses=upcoming_courses)

@app.route('/courses')
def courses():
    return render_template('Mobius.html')


if __name__ == "__main__":
    # Local development only. On Railway, gunicorn imports `app` directly.
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)