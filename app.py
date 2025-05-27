from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session # Added flash and session
import sqlite3
import datetime
import os

# New Imports for Authentication
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Try to get SECRET_KEY from environment variable, otherwise use a fallback for local development
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_fallback_secret_key')
DATABASE = 'database.db'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # This tells Flask-Login where to redirect if login is required

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def get_id(self): # Required by Flask-Login, returns a unique ID for the user
        return str(self.id)

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    # Fetch user data from your 'users' table
    user_data = conn.execute('SELECT id, username, password_hash, role FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['password_hash'], user_data['role'])
    return None

# --- Routes for Patients ---

@app.route('/')
def index():
    """Main page for patients to view available slots and book."""
    conn = get_db_connection()
    # For MVP, we'll just show *some* available times.
    # In a real app, you'd fetch provider availability, etc.
    available_times = [
        "2025-06-01 10:00", "2025-06-01 11:00", "2025-06-01 14:00",
        "2025-06-02 09:30", "2025-06-02 10:30"
    ]
    
    # Fetch already booked times to exclude them
    booked_appointments_db = conn.execute('SELECT appointment_time FROM appointments').fetchall()
    booked_times = [row['appointment_time'] for row in booked_appointments_db]

    # Filter out booked times
    available_slots = [time for time in available_times if time not in booked_times]
    
    conn.close()
    return render_template('index.html', available_slots=available_slots)

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    """Handles new appointment booking."""
    patient_name = request.form['patient_name']
    patient_phone = request.form['patient_phone']
    patient_email = request.form['patient_email']
    appointment_time = request.form['appointment_time']

    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO appointments (patient_name, patient_phone, patient_email, appointment_time) VALUES (?, ?, ?, ?)',
            (patient_name, patient_phone, patient_email, appointment_time)
        )
        conn.commit()
        # In a real app, send confirmation email/SMS here
        # print(f"Sending confirmation to {patient_email} for {appointment_time}")
        return redirect(url_for('success_page', name=patient_name, time=appointment_time))
    except sqlite3.IntegrityError:
        # This occurs if the appointment_time (which is UNIQUE) is already taken
        return "Sorry, that time slot is no longer available. Please go back and choose another.", 400
    finally:
        conn.close()

@app.route('/success')
def success_page():
    name = request.args.get('name')
    time = request.args.get('time')
    return f"Appointment booked successfully for {name} at {time}! Check your email/phone for confirmation."

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # If user is already logged in, redirect
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user_data = conn.execute('SELECT id, username, password_hash, role FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user_data:
            user = User(user_data['id'], user_data['username'], user_data['password_hash'], user_data['role'])
            if check_password_hash(user.password_hash, password):
                login_user(user) # Log the user in
                # flash('Logged in successfully!', 'success') # Optional: show a success message
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password.', 'error') # Show error for wrong password
        else:
            flash('Invalid username or password.', 'error') # Show error for wrong username

    return render_template('login.html')

@app.route('/logout')
@login_required # User must be logged in to log out
def logout():
    logout_user() # Log the user out
    flash('You have been logged out.', 'info') # Optional: show a message
    return redirect(url_for('index')) # Redirect to home page after logout

# --- Routes for Admin (VERY BASIC) ---

@app.route('/admin')
@login_required # THIS LINE PROTECTS THE ROUTE
def admin_dashboard():
    """Basic admin view to see all appointments."""
    conn = get_db_connection()
    appointments = conn.execute('SELECT * FROM appointments ORDER BY appointment_time DESC').fetchall()
    conn.close()
    return render_template('admin.html', appointments=appointments)

@app.route('/admin/update_status/<int:appointment_id>', methods=['POST'])
@login_required # THIS LINE PROTECTS THE ROUTE
def update_appointment_status(appointment_id):
    """Allows admin to update an appointment's status."""
    new_status = request.form['status']
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (new_status, appointment_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True) # debug=True allows automatic reloading and provides debugging info