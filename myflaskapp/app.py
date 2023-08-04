from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import json
from web3.auto import w3
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from geopy.geocoders import Nominatim
import random
from math import radians, sin, cos, sqrt, atan2



#pass email Pc_123456
app = Flask(__name__)

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['users']
purchase_collection = db['energy_purchase']
hasil_pemilihan_peer_collection = db['hasil_pemilihan_peer']

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

             # Generate a random initial energy value between 0 and 800
        current_energy = random.randint(0, 800)
        energy_sold = 0
        energy_purchased = 0

        # Save the user data to the database, including the coordinates, address, and energy balance
        user_data = {
            'name': name,
            'email': email,
            'username': username,
            'password': password,
            'geo_coordinates': coordinates,  # Saving the coordinates from Geopy
            'geo_address': geo_address,  # Saving the address from Geopy
            'current_energy': current_energy,  # Saving the generated energy balance
            'energy_sold': energy_sold,  # Set energy_sold to 0 upon registration
            'energy_purchased': energy_purchased,  # Set energy_purchased to 0 upon registration
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
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Retrieve the data for the dashboard from your database or any other source
    

    # Connect to Ganache and retrieve the ethereum balance and used values
    ganache_account = w3.eth.accounts[0]
    ethereum_balance_wei = w3.eth.get_balance(ganache_account)
    ethereum_balance = w3.from_wei(ethereum_balance_wei, 'ether')

    # Retrieve the amount of Ethereum used from Ganache
    ethereum_used_wei = w3.eth.get_transaction_count(ganache_account)
    ethereum_used = w3.from_wei(ethereum_used_wei, 'ether')

    # Get the energy balance from the database for the logged-in user
    user_data = collection.find_one({'username': session['username']})
    current_energy = user_data['current_energy']
    energy_sold = user_data['energy_sold']
    energy_purchased = user_data['energy_purchased']
    
    
    # You can do the same for the ethereum_used value if needed
    return render_template('dashboard.html', energy_sold=f"{energy_sold} kWh", energy_purchased=f"{energy_purchased} kWh", current_energy=f"{current_energy} kWh", ethereum_balance=f"{ethereum_balance} kWh", ethereum_used=f"{ethereum_used} kWh")

#Peers
@app.route('/peers')
@is_logged_in
def peers():
    # Mengambil informasi pengguna dari basis data
    users = collection.find()

    return render_template('peers.html', users=users)



def calculate_distance(coord1, coord2):
    lat1, lon1 = map(float, coord1.split())
    lat2, lon2 = map(float, coord2.split())

    # Convert latitude and longitude from degrees to radians
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_km = 6371 * c

    return distance_km

@app.route('/purchase', methods=['GET', 'POST'])
@is_logged_in
def purchase():
    if request.method == 'POST':
        # Get user data from the database
        user_data = collection.find_one({'username': session['username']})
        user_id = user_data['_id']  # Get the user ID from the database
        username = user_data['username']  # Get the username from the database

        # Get amount from the form and convert it to integer
        amount_requested = int(request.form['amount'])

        # Save energy purchase data to the "energy_purchase" collection
        purchase_data = {
            'user_id': user_id,
            'amount': amount_requested
        }
        purchase_collection.insert_one(purchase_data)

        # Retrieve the buyer's coordinates from the user_data
        buyer_coordinates = user_data['geo_coordinates']

        # Retrieve all sellers' data from the database
        all_sellers = collection.find()

        # Create a list to store the sellers' data along with their distances from the buyer
        sellers_with_distance = []

        # Calculate the distance of each seller from the buyer using the calculate_distance function
        for seller in all_sellers:
            seller_id = seller['_id']
            seller_coordinates = seller['geo_coordinates']
            energy_balance = int(seller['current_energy'])  # Convert energy_balance to integer

            # Skip the buyer (peer) from being considered as a seller
            if seller_id == user_id:
                continue

            distance = calculate_distance(buyer_coordinates, seller_coordinates)
            sellers_with_distance.append((seller_id, seller_coordinates, distance, energy_balance, seller['username']))

        # Sort sellers by distance in ascending order
        sellers_with_distance.sort(key=lambda x: x[2])

        # Initialize variables for tracking selected sellers and total energy taken
        selected_sellers_list = []
        total_energy_taken = 0

        # Iterate through sellers with distance and select sellers with enough energy to fulfill the request
        for seller_id, seller_coordinates, distance, energy_balance, seller_username in sellers_with_distance:
            # Check if the seller has enough energy to fulfill the request
            if energy_balance > 0 and total_energy_taken < amount_requested:
                # Calculate the amount of energy to be taken from this seller
                energy_taken = min(amount_requested - total_energy_taken, energy_balance)

                # Add the selected seller's data to the selected_sellers_list
                selected_seller_data = {
                    'seller_id': seller_id,
                    'energy_taken': energy_taken,
                    'buyer_id': user_id,
                    'buyer_username': username,  # Add the buyer's username
                    'seller_username': seller_username,  # Add the seller's username
                    'seller_coordinates': seller_coordinates,
                    'distance': distance
                }
                selected_sellers_list.append(selected_seller_data)

                # Update total energy taken
                total_energy_taken += energy_taken

        # Save selected sellers' data to the "Hasil Pemilihan Peer" database
        hasil_pemilihan_peer_collection.insert_many(selected_sellers_list)

        flash('Your order is being processed', 'success')
        return redirect(url_for('dashboard'))

    return render_template('purchase.html')



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)