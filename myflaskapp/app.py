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
from geopy.distance import geodesic
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, validators
from flask_wtf.csrf import CSRFProtect, CSRFError,generate_csrf, validate_csrf
from operator import itemgetter


#pass email Pc_123456
app = Flask(__name__)


# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['users']
purchase_collection = db['energy_purchase']
peer_selection_collection = db['peer_selection']
seller_notifications = db['seller_notifications']  # Koleksi untuk menyimpan notifikasi penjual

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
@app.route('/dashboard', methods=['GET', 'POST'])
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

   

    # Render the dashboard template with the form
    return render_template(
    'dashboard.html',
    energy_sold=f"{energy_sold} kWh",
    energy_purchased=f"{energy_purchased} kWh",
    current_energy=f"{current_energy} kWh",
    ethereum_balance=f"{ethereum_balance} ETH",
    ethereum_used=f"{ethereum_used} kWh",
)


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

    # Use geodesic from geopy to calculate the distance
    distance_km = geodesic((lat1, lon1), (lat2, lon2)).kilometers
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

        # Retrieve the buyer's coordinates from the user_data
        buyer_coordinates = user_data['geo_coordinates']

        # Retrieve all sellers' data from the database
        all_sellers = collection.find()

        # Create lists to store single and multiple sellers' data
        single_sellers_list = []
        multiple_sellers_list = []

        # Calculate the distance of each seller from the buyer using the calculate_distance function
        for seller in all_sellers:
            seller_id = seller['_id']
            seller_coordinates = seller['geo_coordinates']
            energy_balance = int(seller['current_energy'])  # Convert energy_balance to integer

            # Skip the buyer (peer) from being considered as a seller
            if seller_id == user_id:
                continue

            # Check if the seller has enough energy to fulfill the request
            if energy_balance >= amount_requested:
                distance = calculate_distance(buyer_coordinates, seller_coordinates)

                # Add the seller's data to the single_sellers_list
                seller_data = {
                    'user_id': seller_id,
                    'username': seller['username'],
                    'status': 'PENDING',
                    'urutan/ranking': None,
                    'amount': amount_requested,  # Store the requested amount
                    'energy_taken': amount_requested,  # Store the actual energy taken (requested amount)
                    'provider_type': 'SINGLE',  # Store the provider type as SINGLE
                    'distance': distance  # Store the distance from the buyer
                }
                single_sellers_list.append(seller_data)
            else:
                # Add the seller's data to the multiple_sellers_list
                seller_data = {
                    'user_id': seller_id,
                    'username': seller['username'],
                    'status': 'PENDING',
                    'urutan/ranking': None,
                    'amount': amount_requested,  # Store the requested amount
                    'energy_taken': energy_balance,  # Store the actual energy taken (available energy)
                    'provider_type': 'MULTIPLE',  # Store the provider type as MULTIPLE
                    'distance': None  # Distance is not applicable for MULTIPLE providers
                }
                multiple_sellers_list.append(seller_data)

        # If there are single sellers, sort the single_sellers_list based on distance
        if single_sellers_list:
            single_sellers_list.sort(key=itemgetter('distance'))

        # Combine single and multiple sellers' lists
        selected_sellers_list = single_sellers_list + multiple_sellers_list

        # Create the peer selection document
        peer_selection_document = {
            'amount': amount_requested,
            'buyer_id': user_id,
            'buyer_username': username,
            'provider_type': 'SINGLE' if single_sellers_list else 'MULTIPLE',  # Determine provider type
            'candidate': selected_sellers_list  # Store the combined list of sellers
        }

        # Save the peer selection document to the "peer_selection" collection
        peer_selection_collection.insert_one(peer_selection_document)

        # Create notifications for selected sellers and save them to the "seller_notifications" collection
        for seller in selected_sellers_list:
            # Create a notification document
            notification_data = {
                'buyer_name': username,
                'energy_taken': seller['energy_taken'],
                'status': 'PENDING',
                'seller_id': seller['user_id']  # Include the seller's ID for reference
            }

            # Save the notification document to the "seller_notifications" collection
            seller_notifications.insert_one(notification_data)

        flash('Your order is being processed', 'success')
        return redirect(url_for('dashboard'))

    return render_template('purchase.html')




@app.route('/notifications_seller', methods=['GET', 'POST'])
@is_logged_in
def notifications_seller():
    # Dapatkan ID pengguna dari sesi
    user_id = collection.find_one({'username': session['username']})['_id']

    if request.method == 'POST':
        # Handle the "Approve" action
        if 'approve' in request.form:
            # Proses aksi "Approve" di sini
            # Misalnya, Anda dapat mengubah status notifikasi menjadi "APPROVED"
            # dan melakukan tindakan lain yang sesuai
            notification_id = request.form['approve']  # ID notifikasi yang di-approve
            peer_selection_collection.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {'status': 'APPROVED'}}
            )
            flash('Notification approved successfully', 'success')

        # Handle the "Decline" action
        elif 'decline' in request.form:
            # Proses aksi "Decline" di sini
            # Misalnya, Anda dapat mengubah status notifikasi menjadi "DECLINED"
            # dan melakukan tindakan lain yang sesuai
            notification_id = request.form['decline']  # ID notifikasi yang di-decline
            peer_selection_collection.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {'status': 'DECLINED'}}
            )
            flash('Notification declined successfully', 'success')

        return redirect(url_for('notifications_seller'))

    # Dapatkan notifikasi yang sesuai dengan kriteria
    selected_sellers = peer_selection_collection.find({
        'buyer_id': user_id,
        'status': 'PENDING'
    })

    # Filter notifikasi berdasarkan tipe penyedia energi
    single_notifications = []
    multiple_notifications = []

    for notification in selected_sellers:
        if notification['provider_type'] == 'SINGLE':
            if len(single_notifications) == 0:
                single_notifications.append(notification)
        elif notification['provider_type'] == 'MULTIPLE':
            multiple_notifications.append(notification)

    # Render template HTML dengan notifikasi yang sesuai
    return render_template('notifications_seller.html',
                           single_notifications=single_notifications,
                           multiple_notifications=multiple_notifications)



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)