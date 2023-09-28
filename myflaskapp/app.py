import random
from bson import ObjectId
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from passlib.hash import sha256_crypt
from functools import wraps
from web3 import Web3
from web3.auto import w3
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from wtforms import Form, StringField, PasswordField, validators, StringField, validators

#pass email Pc_123456
app = Flask(__name__)
CSRFProtect(app)

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
user_collection = db['users']
seller_notifications_collection = db['seller_notifications']  # Koleksi untuk menyimpan notifikasi penjual
purchase_order_collection = db['peer_selection']

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
        if user_collection.find_one({'email': email}):
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
        user_collection.insert_one(user_data)

        # Menghubungkan dengan akun Ganache
        accounts = w3.eth.accounts
        bcaddress = accounts[0]
        user_collection.update_one(
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
        user = user_collection.find_one({'username': username})

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
    user_data = user_collection.find_one({'username': session['username']})
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
    users = user_collection.find()

    return render_template('peers.html', users=users)



def calculate_distance(coord1, coord2):
    lat1, lon1 = map(float, coord1.split())
    lat2, lon2 = map(float, coord2.split())

    # Use geodesic from geopy to calculate the distance
    distance_km = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    return distance_km

def get_candidates(user_id, buyer_coordinates, amount_requested):
    # get all peers that has energy & not the current active user
    peers = user_collection.find({ 'energy_balance': { '$gt': 0 }, '_id': { '$ne': ObjectId(user_id) } })
    candidates = []

    for seller in peers:
        energy_balance = int(seller['current_energy'])  # Convert energy_balance to integer
        seller_id = seller['_id']
        seller_username = seller['username']
        seller_coordinates = seller['geo_coordinates']
        distance = calculate_distance(buyer_coordinates, seller_coordinates)

        candidates.append({
            'user_id': seller_id,
            'username': seller_username,
            'distance': distance,
            'availabel_energy': energy_balance,
            'energy_taken': 0
        })

    return candidates

# get candidates for MULTIPLE provide type
def get_selected_candidates(candidates, amount_requested):
    selected_candidates = []
    total_energy_taken = 0
    for candidate in candidates:
        if (total_energy_taken >= amount_requested):
            break

        energy_needs = amount_requested - total_energy_taken
        energy_balance = candidate['available_energy']
        energy_taken = min(energy_needs, energy_balance)

        candidate['energy_taken'] = energy_taken
        total_energy_taken += energy_taken

    return selected_candidates

def update_candidate_energy_taken_and_status(candidate, purchase_order):
    purchase_order_collection.update_one(
        { '_id': ObjectId(purchase_order['_id']), 'candidate.user_id': candidate['user_id'] },
        { '$set': {
                'candidate.$.status': 'PENDING',
                'candidate.$.energy_taken': candidate['energy_taken']
            }
        }
    )


def create_notification(purchase_order, candidate, energy_taken):
    notification = {
        'purchase_id': purchase_order['_id'],
        'buyer_username': purchase_order['buyer_username'],
        'seller_id': candidate['user_id'],
        'seller_username': candidate['username'],
        'energy_taken': energy_taken,
        'status': 'PENDING'
    }
    seller_notifications_collection.insert_many(notification)

@app.route('/purchase', methods=['POST'])
@is_logged_in
def purchase():
    # Get user data from the database
    user_data = user_collection.find_one({'username': session['username']})
    user_id = user_data['_id']  # Get the user ID from the database
    username = user_data['username']  # Get the username from the database
    amount_requested = int(request.form['amount'])

    purchase_order = {
        'amount': amount_requested,
        'buyer_id': user_id,
        'buyer_username': username,
        'amount_requested': amount_requested
    }
    created_purchase_order = purchase_order_collection.insert_one(purchase_order)
    purchase_order = purchase_order_collection.find_one(created_purchase_order.inserted_id)

    buyer_coordinates = user_data['geo_coordinates']
    candidates = get_candidates(user_id, buyer_coordinates, amount_requested)

    # calculate total available energy from all candidates
    available_energies = map(lambda c: c['availabel_energy'], candidates)
    total_available_energy = sum(available_energies)
    if (total_available_energy < amount_requested):
        flash('Requested amount cannot be fulfiled', 'danger')
        return

    # sort candidates by distance
    candidates.sort(key = lambda c: c['distance'])

    # SINGLE if the nearest candidate can fulfill all requested amount
    provider_type = 'SINGLE' if candidates[0]['available_energy'] >= amount_requested else 'MULTIPLE'
    purchase_order_collection.update_one(
        { '_id': ObjectId(created_purchase_order.inserted_id) },
        { '$set': {
                'candidate': candidates ,
                'provider_type': provider_type
            }
        }
    )

    if (provider_type == 'SINGLE'):
        candidates[0]['energy_taken'] = amount_requested
        update_candidate_energy_taken_and_status(candidates[0])
        create_notification(candidates[0])
    else:
        selected_candidates = get_selected_candidates(candidates, amount_requested)
        for sc in selected_candidates:
            update_candidate_energy_taken_and_status(sc)
            create_notification(sc)

    flash('Your order is being processed', 'success')

    # Redirect to the dashboard page
    return redirect(url_for('dashboard'))


@app.route('/purchase', methods=['GET'])
@is_logged_in
def open_purchase_page():
    return render_template('purchase.html')

@app.route('/notifications_seller', methods=['GET'])
@is_logged_in
def notifications_seller():
    # Dapatkan ID pengguna dari sesi
    user_id = user_collection.find_one({'username': session['username']})['_id']

    # Dapatkan notifikasi yang sesuai dengan kriteria
    notifications = seller_notifications_collection.find({
        'seller_id': user_id,
        'status': 'PENDING'
    })

    # Render template HTML dengan notifikasi yang sesuai
    return render_template('notifications_seller.html', notifications = notifications)

@app.route('/purchase-requests', methods=['POST'])
@is_logged_in
def decline_request():
    notification_id = request.form['notification_id']  # ID notifikasi yang di-approve
    purchase_id = request.form['purchase_id']
    seller_id = request.form['seller_id']

    if 'approve' in request.form:
        # Proses aksi "Approve" di sini
        # Misalnya, Anda dapat mengubah status notifikasi menjadi "APPROVED"
        # dan melakukan tindakan lain yang sesuai
        seller_notifications_collection.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'status': 'APPROVED'}}
        )

        purchase_order_collection.update_one(
            {'_id': ObjectId(purchase_id), 'candidate.user_id': seller_id},
            {'$set': {'candidate.$.status': 'APPROVED'}}
        )

        flash('Notification approved successfully', 'success')

        # TODO do energy transfer
        # TODO do transaction to ether

    # Handle the "Decline" action
    elif 'decline' in request.form:
        # Proses aksi "Decline" di sini
        # Misalnya, Anda dapat mengubah status notifikasi menjadi "DECLINED"
        # dan melakukan tindakan lain yang sesuai
        seller_notifications_collection.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'status': 'DECLINED'}}
        )

        purchase_order_collection.update_one(
            {'_id': ObjectId(purchase_id), 'candidate.user_id': seller_id},
            {'$set': {'candidate.$.status': 'DECLINED'}}
        )

        flash('Notification declined successfully', 'success')

        # TODO re-calculate candidates

    return redirect (url_for('notifications_seller'))




if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)