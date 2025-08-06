from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)

# Load Flask secret key and MongoDB URI from environment variables
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
mongo_uri = os.environ.get('MONGODB_URI')

if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY not set in environment.")
if not mongo_uri:
    raise ValueError("MONGODB_URI not set in environment.")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['DecodeX']
users_collection = db['users']
history_collection = db['history']

@app.route('/')
def home():
    return render_template('getstarted.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    output = ""
    if request.method == 'POST':
        # Instead of executing the code, just save it as a snippet or note
        code = request.form['code']
        output = "Code saved (execution disabled for security)."

        history_collection.insert_one({
            'username': session['username'],
            'time': datetime.now(),
            'input': code,
            'output': output
        })

    user_history = history_collection.find({'username': session['username']})
    return render_template('index.html', output=output, history=user_history)

@app.route('/history')
def history():
    if 'username' not in session:
        flash('Please log in to access your history.')
        return redirect(url_for('login'))

    user_history = history_collection.find({'username': session['username']})
    return render_template('history.html', history=user_history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password cannot be empty')
            return redirect(url_for('login'))

        user = users_collection.find_one({'username': username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not username or not email or not password:
            flash('All fields are required')
            return redirect(url_for('signup'))

        if '@' not in email:
            flash('Invalid email format')
            return redirect(url_for('signup'))

        if users_collection.find_one({'username': username}):
            flash('Username already exists!')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })

        flash('Signup successful! Please login.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
