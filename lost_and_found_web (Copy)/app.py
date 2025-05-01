import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash # More secure password handling
from werkzeug.utils import secure_filename
from functools import wraps
import datetime

# --- Configuration ---
DATABASE_USER = "users.db"
DATABASE_ITEM = "lost_and_found.db"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
SECRET_KEY = 'crazyskull' # CHANGE THIS! Generate a real secret key

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit uploads to 16MB

# --- Database Functions ---

# User DB
def get_user_db():
    db = getattr(g, '_user_database', None)
    if db is None:
        db = g._user_database = sqlite3.connect(DATABASE_USER)
        db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return db

# Item DB
def get_item_db():
    db = getattr(g, '_item_database', None)
    if db is None:
        db = g._item_database = sqlite3.connect(DATABASE_ITEM)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    user_db = getattr(g, '_user_database', None)
    if user_db is not None:
        user_db.close()
    item_db = getattr(g, '_item_database', None)
    if item_db is not None:
        item_db.close()

def init_db():
    # Initialize Item DB
    conn_item = sqlite3.connect(DATABASE_ITEM)
    cursor_item = conn_item.cursor()
    cursor_item.execute('''CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        location TEXT,
                        time TEXT,
                        contact TEXT NOT NULL,
                        image_filename TEXT, -- Store only filename
                        reporter_user_id INTEGER)''') # Optional: link to user
    conn_item.commit()
    conn_item.close()

    # Initialize User DB
    conn_user = sqlite3.connect(DATABASE_USER)
    cursor_user = conn_user.cursor()
    cursor_user.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL)''') # Store hash, not plain password
    conn_user.commit()
    conn_user.close()
    print("Databases Initialized.")

# Run this once manually or check if DB exists before running app
# init_db() # Uncomment to initialize if needed, then comment out again

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_user_db()
        cursor = db.cursor()

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('register.html')

        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists. Please choose another.', 'warning')
            return render_template('register.html')
        else:
            hashed_password = generate_password_hash(password)
            try:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                               (username, hashed_password))
                db.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.Error as e:
                 flash(f'Database error during registration: {e}', 'danger')
                 return render_template('register.html')


    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_user_db()
        cursor = db.cursor()

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/report/<category>', methods=['GET', 'POST'])
@login_required
def report_item(category):
    if category not in ['Lost', 'Found']:
        flash('Invalid category.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        description = request.form['description']
        location = request.form['location']
        time = request.form['time']
        contact = request.form['contact']
        image_filename = None # Default to no image

        if not description or not contact:
             flash('Description and Contact information are required.', 'danger')
             return render_template('report_item.html', category=category)

        # --- Handle Image Upload ---
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '': # Check if a file was actually selected
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename) # Sanitize filename
                    # Ensure uploads directory exists
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    # Prevent overwrites by adding user_id or timestamp if needed (simplification here)
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(save_path)
                    image_filename = filename # Store the filename in DB
                else:
                    flash('Invalid image file type. Allowed types: png, jpg, jpeg, gif', 'warning')
                    return render_template('report_item.html', category=category)


        # --- Insert into Database ---
        db = get_item_db()
        cursor = db.cursor()
        try:
            cursor.execute("""INSERT INTO items
                           (category, description, location, time, contact, image_filename, reporter_user_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                           (category, description, location, time, contact, image_filename, session['user_id']))
            db.commit()
            flash(f'{category} item reported successfully!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.Error as e:
            flash(f'Database error reporting item: {e}', 'danger')
            # Consider deleting the uploaded file if DB insert fails
            # if image_filename and os.path.exists(save_path):
            #     os.remove(save_path)
            return render_template('report_item.html', category=category)


    # For GET request
    return render_template('report_item.html', category=category)

@app.route('/view/<category>')
@login_required
def view_items(category):
    if category not in ['Lost', 'Found']:
        flash('Invalid category.', 'danger')
        return redirect(url_for('dashboard'))

    db = get_item_db()
    cursor = db.cursor()
    cursor.execute("SELECT description, location, time, contact, image_filename FROM items WHERE category=?", (category,))
    items = cursor.fetchall() # Fetches all matching rows as Row objects

    return render_template('view_items.html', items=items, category=category)

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Main Execution ---
if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # Check if DBs exist, if not, initialize
    if not os.path.exists(DATABASE_USER) or not os.path.exists(DATABASE_ITEM):
         print("One or both database files not found. Initializing...")
         init_db()
    # Run the app in debug mode (convenient for development)
    # Use a proper WSGI server like Gunicorn or Waitress for deployment
    app.run(debug=True)