from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import json
from web3 import Web3
from web3.auto import w3
from geopy.geocoders import Nominatim
#pass email Pc_123456
app = Flask(__name__)

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['users']
purchase_collection = db['energy_purchase']

# Koneksi ke Ganache
w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))

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
    # Modify the field for coordinates
    coordinates = StringField('Coordinates', [validators.DataRequired()])


# Route untuk halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        coordinates = form.coordinates.data  # Get the coordinates from the form

        # Use Geopy to validate and process the coordinates if needed
        geolocator = Nominatim(user_agent="myGeocoder")
        location = geolocator.reverse(coordinates)
        geo_address = location.address if location else ""

        # Check if the email is already registered
        if collection.find_one({'email': email}):
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('register.html', form=form)

        # Save the user data to the database, including the coordinates and address
        user_data = {
            'name': name,
            'email': email,
            'username': username,
            'password': password,
            'geo_coordinates': coordinates,  # Saving the coordinates from Geopy
            'geo_address': geo_address  # Saving the address from Geopy
        }
        collection.insert_one(user_data)

        # Menghubungkan dengan akun Ganache
        accounts = w3.eth.accounts
        bcaddress = accounts[0]
        collection.update_one(
            {'username': username},
            {'$set': {'bcaddress': bcaddress}}  # Saving the Ganache address (bcaddress)
        )

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
     # Retrieve the data for the dashboard from your database or any other source
    energy_sold = "250 kWh"
    energy_purchased = "150 kWh"
    current_energy = "100 kWh"
    ethereum_balance = "2.5 ETH"
    ethereum_used = "1.8 ETH"
    return render_template('dashboard.html', energy_sold=energy_sold, energy_purchased=energy_purchased, current_energy=current_energy, ethereum_balance=ethereum_balance, ethereum_used=ethereum_used)

#Peers
@app.route('/peers')
@is_logged_in
def peers():
    # Mengambil informasi pengguna dari basis data
    users = collection.find()

    return render_template('peers.html', users=users)


@app.route('/purchase', methods=['GET', 'POST'])
@is_logged_in
def purchase():
    if request.method == 'POST':
        # Get user data from the database
        user_data = collection.find_one({'username': session['username']})
        user_id = user_data['_id']  # Get the user ID from the database

        # Get amount from the form
        amount = request.form['amount']

        # Save energy purchase data to the "energi_pembelian" collection
        purchase_data = {
            'user_id': user_id,  # Save the user ID in the "energi_pembelian" collection
            'amount': amount
        }
        purchase_collection.insert_one(purchase_data)

        flash('Your order is being processed', 'success')
        return redirect(url_for('dashboard'))

    return render_template('purchase.html')
    

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)