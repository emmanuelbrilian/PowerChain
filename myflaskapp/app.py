from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['users']

#Index
@app.route('/')
def index():
    return render_template('home.html')

#About
@app.route('/about')
def about():
    return render_template('about.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password Do Not Match')
    ])
    confirm = PasswordField('Confirm Password')

# Route untuk halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Memasukkan data pengguna ke dalam basis data MongoDB
        user_data = {
            'name': name,
            'email': email,
            'username': username,
            'password': password
        }
        collection.insert_one(user_data)

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

#userlogin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Mengambil data dari form
        username = request.form['username']
        password_candidate = request.form['password']

        # Mencari pengguna berdasarkan username
        user = collection.find_one({'username': username})

        if user:
            # Mendapatkan password yang disimpan
            stored_password = user['password']

            # Membandingkan password
            if sha256_crypt.verify(password_candidate, stored_password):
                #passed
                session["logged_in"] = True
                session["username"] = username

                flash("You are now logged in", "success")
                return redirect(url_for('dashboard'))
                
                # Login berhasil
                # Lakukan tindakan yang diperlukan, seperti mengatur sesi atau mengarahkan pengguna ke halaman beranda
            else:
                error = "invalid login"
                return render_template ("login.html", error=error)
            

        else:
            error = "Username not found"
            return render_template ("login.html", error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect (url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
        session.clear()
        flash('You are now logged out', 'success')
        return redirect(url_for('login'))

# Dashboard
@app.route ('/dashboard')
@is_logged_in 
def dashboard():
    return render_template ('dashboard.html')

#Peers
@app.route('/peers')
@is_logged_in
def peers():
    # Mengambil informasi pengguna dari basis data
    users = collection.find()

    return render_template('peers.html', users=users)
    

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)