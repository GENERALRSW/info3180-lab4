import os
from app import app, db
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from app.models import UserProfile
from app.forms import LoginForm, UploadForm

# Ensure the upload folder exists on startup
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="Mary Jane")


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Query the database for a matching username
        user = UserProfile.query.filter_by(username=username).first()

        # Check that user exists and password is correct
        if user is not None and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful! Welcome back, {}.'.format(user.first_name), 'success')
            return redirect(url_for('upload'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        upload_path = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, filename))
        flash('File "{}" uploaded successfully!'.format(filename), 'success')
        return redirect(url_for('upload'))

    return render_template('upload.html', form=form)


def get_uploaded_images():
    """Iterate over the uploads folder and return a list of image filenames."""
    images = []
    upload_folder = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])

    for subdir, dirs, files in os.walk(upload_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(file)

    return images


@app.route('/uploads/<filename>')
@login_required
def get_image(filename):
    """Return a specific image from the uploads folder."""
    return send_from_directory(
        os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER']),
        filename
    )


@app.route('/files')
@login_required
def files():
    """Display all uploaded images in a grid."""
    images = get_uploaded_images()
    return render_template('files.html', images=images)


###
# The functions below should be applicable to all Flask apps.
###

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')


@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404
