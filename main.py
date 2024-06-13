from flask import (Flask, abort, render_template,
                   redirect, url_for, flash, send_from_directory, request, make_response, send_file)
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, LargeBinary, Column
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os


app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI','sqlite:///projects.db')

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))







class ProjectPost(db.Model):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    img = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    mimetype = Column(Text, nullable=False)
    project_url = Column(String(250), nullable=False)


with app.app_context():
    db.create_all()

# def read_image(file_path):
#     with open(file_path, 'rb') as file:
#         return file.read()
#
# def store_image_in_db(image_data,session):
#     new_image = ProjectPost(data=image_data)
#     session.add(new_image)
#     session.commit()

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    current_year = datetime.datetime.now().year
    result = db.session.execute(db.select(ProjectPost))
    projects = result.scalars().all()
    return render_template('index.html', projects=projects, current_year=current_year)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email==email))
        user = result.scalar()
        if user:
            flash("You have already registered, log in instead")
            return redirect(url_for("login"))

        new_user = User(
            email=form.email.data,
            password= form.password.data,

        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)

@app.route('/image/<int:image_id>')
def get_img(image_id):
    image = ProjectPost.query.get(image_id)
    if image is None:
        abort(404)
    response = make_response(image.img)
    response.headers.set('Content-Type','image/png')
    response.headers.set('Content-Disposition', 'inline', filename=image.name)
    return response


@app.route('/adminilkin1994',methods=["GET", "POST"])
def backdoor():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            flash("The email or password dont exist. Please try again!")
            return redirect(url_for("register"))
        elif password != user.password:
            flash('Password incorrect, please try again.')
            return redirect(url_for('backdoor'))
        elif password==user.password:
            login_user(user)
            return redirect(url_for("home"))

    return render_template('back.html', form=form, logged_in=current_user.is_authenticated)

@app.route('/add_project', methods=['GET','POST'])
def add_project():
    return render_template('add-project.html')

@app.route('/upload', methods=['POST'])
def upload():

        pic = request.files['pic']
        if not pic:
            flash('No pic uploaded'), 400

        file_name = secure_filename(pic.filename)
        mimetype = pic.mimetype
        new_project = ProjectPost(
            img=pic.read(),
            name=file_name,
            mimetype=mimetype,
            project_url=request.form['url']

        )
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('home'))





@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete/<int:project_id>")
@admin_only
def delete(project_id):
    project_to_delete = db.get_or_404(ProjectPost, project_id)
    db.session.delete(project_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/update/<int:project_id>", methods=["GET", "POST"])
@admin_only
def update(project_id):
    project = db.get_or_404(ProjectPost, project_id)

    if request.method == "POST":
        pic = request.files['pic']

        if not pic:
            flash('No pic uploaded')
            return redirect(request.url)

        file_name = secure_filename(pic.filename)
        mimetype = pic.mimetype

        project.img = pic.read()
        project.name = file_name
        project.mimetype = mimetype
        project.project_url = request.form['url']

        db.session.commit()
        return redirect(url_for('home'))

    return render_template('update-project.html', project=project)


@app.route('/download', methods=['GET', 'POST'])
def download():
    path_to_resume = 'static/resume/resume.pdf'
    return send_file(path_to_resume, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=False, port=5002)