import sqlite3
import os
from flask import render_template, request, redirect, flash, session, url_for, Blueprint, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

bp = Blueprint('app', __name__)

# Create a database connection
def create_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Rows behave like dictionaries
    return conn

# Home Route (Redirects to login)
@bp.route('/')
def home():
    return redirect(url_for('app.login'))

# Login Route
# Login Route
# Login Route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if login is for admin (corrected email and password)
        if email == 'admin100@gmail.com' and password == 'admin123':
            session['user_id'] = 'admin'  # Mark session as admin
            return redirect(url_for('app.admin_dashboard'))  # Redirect to admin dashboard

        # Check for consumer login (from the database)
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect(url_for('app.dashboard'))
        else:
            flash("Invalid credentials", "error")

    return render_template('login.html')


# Admin Dashboard Route
@bp.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # Check if the user is admin
    if session.get('user_id') != 'admin':
        return redirect(url_for('app.login'))  # Redirect to login if not admin
    
    # Admin Dashboard Page Content
    return render_template('admin_dashboard.html')


@bp.route('/get_dashboard_counts', methods=['GET'])
def get_dashboard_counts():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Sensors")
    total_sensors = cursor.fetchone()[0]

    conn.close()
    return jsonify({'total_users': total_users, 'total_sensors': total_sensors})


# Manage Users Route (Example)
@bp.route('/manage_users', methods=['GET'])
def manage_users():
    if session.get('user_id') != 'admin':
        return redirect(url_for('app.login'))  # Redirect to login if not admin

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")  # Get all users
    users = cursor.fetchall()

    return render_template('manage_users.html', users=users)


# Register Route
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("User already exists!", "error")
        else:
            password_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", 
                           (name, email, password_hash))
            conn.commit()
            flash("User created successfully!", "success")
            return redirect(url_for('app.login'))

    return render_template('register.html')

# Dashboard Route
@bp.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('app.login'))
    
    user_id = session['user_id']
    conn = create_connection()
    cursor = conn.cursor()
    
    # Get user details (name, profile pic, etc.)
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    # Get the total number of sensors assigned to the user (using user_id)
    cursor.execute("SELECT COUNT(*) FROM sensors WHERE user_id=?", (user_id,))
    tot_sensors = cursor.fetchone()[0]  # Extract the count
    
    # Render the dashboard with user info and total sensors
    return render_template('dashboard.html', user=user, tot_sensors=tot_sensors)



# User Settings Route
@bp.route('/user_settings', methods=['GET', 'POST'])
def user_settings():
    if 'user_id' not in session:
        return redirect(url_for('app.login'))

    user_id = session['user_id']
    conn = create_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']

        # Handling password change
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Get the current user's details
        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()

        # Check if the current password matches the one in the database
        if check_password_hash(user['password_hash'], current_password):
            # Check if the new password and confirm password match
            if new_password == confirm_password:
                # Hash the new password and update it in the database
                new_password_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (new_password_hash, user_id))
                conn.commit()
                flash("Password updated successfully!", "success")
            else:
                flash("New password and confirmation do not match.", "error")
        else:
            flash("Current password is incorrect.", "error")

        # Handling profile picture upload
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename:
                filename = secure_filename(f"{name}.png")
                profile_pic.save(os.path.join('static', filename))
                cursor.execute("UPDATE users SET profile_pic=? WHERE id=?", (filename, user_id))

        # Updating user details (name, email, address)
        cursor.execute("UPDATE users SET name=?, email=?, address=? WHERE id=?", (name, email, address, user_id))
        conn.commit()

        # Redirect to the user settings page to trigger flash messages
        return redirect(url_for('app.user_settings'))

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    return render_template('user_settings.html', user=user)


# Billing Route
@bp.route('/billing')
def billing():
    if 'user_id' not in session:
        return redirect(url_for('app.login'))  # Redirect to login if not authenticated

    user_id = session.get('user_id')

    # Check if the user is admin
    if user_id == 'admin':
        return render_template('billing.html')  # Admin billing page
    else:
        return render_template('user_billing.html')  # User-specific billing page

# user billing route
@bp.route('/user_billing')
def user_billing():
    user_id = session.get('user_id')  # Ensure the user is logged in
    if not user_id:
        return redirect(url_for('app.login'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch User Details
    cursor.execute("SELECT name, user_type FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    # Fetch Billing Data for the Logged-in User
    cursor.execute("""
        SELECT Bill_id, user_id, amount_due, Payment_status
        FROM Billing
        WHERE user_id = ?""", (user_id,))
    
    billing_data = cursor.fetchall()  # Fetch all user bills
    conn.close()

    # Convert billing data to dictionaries
    bills = [
        {"bill_id": row[0], "water_used": row[1], "totalamt": row[2], "payment_status": row[3]}
        for row in billing_data
    ]

    return render_template('user_billing.html', user=user, billing_data=bills)



# Contact Route
@bp.route('/contact')
def contact():
    if 'user_id' not in session:
        return redirect(url_for('app.login'))

    user_id = session['user_id']
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    # Example contact information
    contact_info = {
        'name': 'WDS system LTD',
        'contact': '+919876543210',
        'email': 'wdscomplaint@gmail.com',
        'location': 'Sample Location, India'
    }

    return render_template('contact.html', user=user, contact_info=contact_info)

# Route to check if the username is available
@bp.route('/check_username', methods=['GET'])
def check_username():
    username = request.args.get('username')
    if not username:
        return jsonify(available=False)  # If no username is provided, assume not available

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name=?", (username,))
    user = cursor.fetchone()

    if user:
        return jsonify(available=False)  # Username already taken
    else:
        return jsonify(available=True)  # Username is available
    
# Logout Route
@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('app.login'))


# Assign Sensors Route
@bp.route('/assign_sensors', methods=['GET', 'POST'])
def assign_sensors():
    if session.get('user_id') != 'admin':
        return redirect(url_for('app.login'))  # Redirect if not admin
    
    conn = create_connection()
    cursor = conn.cursor()

    # Handle form submission for adding or updating sensors
    if request.method == 'POST':
        sensor_id = request.form.get('sensor_id')
        user_id = request.form.get('user_id')
        sensor_type = request.form.get('sensor_type')
        location = request.form.get('location')
        sensor_status = request.form.get('sensor_status')

        if sensor_id:  # Update existing sensor
            cursor.execute("""
                UPDATE sensors
                SET user_id = ?, sensor_type = ?, location = ?, status = ?
                WHERE sensor_id = ?
            """, (user_id, sensor_type, location, sensor_status, sensor_id))
            flash('Sensor updated successfully!', 'success')
        else:  # Add new sensor
            cursor.execute("SELECT MAX(sensor_id) FROM sensors")
            last_sensor_id = cursor.fetchone()[0]
            new_sensor_id = (last_sensor_id + 1) if last_sensor_id else 1  # Increment or start from 1 if no rows exist

            cursor.execute(""" 
                INSERT INTO sensors (sensor_id, user_id, sensor_type, location, status)
                VALUES (?, ?, ?, ?, ?)
            """, (new_sensor_id, user_id, sensor_type, location, sensor_status))
            flash('Sensor added successfully!', 'success')

        conn.commit()
        conn.close()

        # Redirect to avoid form resubmission on refresh
        return redirect(url_for('app.assign_sensors'))

    # Get all sensors and users to display in the form
    cursor.execute("SELECT sensor_id, user_id, sensor_type, location, status FROM sensors")
    sensors = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    cursor.execute("SELECT id, name FROM users")  # Get users for dropdown
    users = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    conn.close()

    return render_template('assign_sensors.html', sensors=sensors, users=users)





# Delete Sensor Route
@bp.route('/delete_sensor/<int:sensor_id>', methods=['GET'])
def delete_sensor(sensor_id):
    if session.get('user_id') != 'admin':
        return redirect(url_for('app.login'))  # Redirect if not admin

    conn = create_connection()
    cursor = conn.cursor()

    # Delete the sensor by its ID
    cursor.execute("DELETE FROM sensors WHERE sensor_id=?", (sensor_id,))
    conn.commit()
    flash('Sensor deleted successfully!', 'success')

    return redirect(url_for('app.assign_sensors'))

# Edit User Route
@bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('user_id') != 'admin':
        return redirect(url_for('app.login'))  # Redirect if not admin

    conn = create_connection()
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('app.manage_users'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form.get('address', '')

        # Update user details
        cursor.execute("""
            UPDATE users
            SET name=?, email=?, address=?
            WHERE id=?
        """, (name, email, address, user_id))
        conn.commit()

        flash("User details updated successfully!", "success")
        return redirect(url_for('app.manage_users'))

    return render_template('edit_user.html', user=user)

@bp.route('/get_user_details/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Get user details
    cursor.execute("SELECT id, name, address FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get sensor details
    cursor.execute("SELECT sensor_id, sensor_type FROM sensors WHERE user_id=?", (user_id,))
    sensors = cursor.fetchall()

    sensor_list = [f"{s['sensor_id']} ({s['sensor_type']})" for s in sensors]
    
    return jsonify({
        "id": user["id"],
        "username": user["name"],
        "address": user["address"],
        "total_sensors": len(sensors),
        "sensors": ", ".join(sensor_list)
    })

@bp.route('/modify_user/<int:user_id>', methods=['POST'])
def modify_user(user_id):
    data = request.json
    new_username = data.get("username")
    new_address = data.get("address")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET name=?, address=? WHERE id=?", (new_username, new_address, user_id))
    conn.commit()

    return jsonify({"message": "User details updated successfully!"})

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Delete user and their sensors
    cursor.execute("DELETE FROM sensors WHERE user_id=?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()

    return jsonify({"message": "User deleted successfully!"})

# Route for consumers to toggle service requests
@bp.route('/request_service', methods=['POST'])
def request_service():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user_id = session['user_id']
    conn = create_connection()
    cursor = conn.cursor()

    # Get current status
    cursor.execute("SELECT service_needed FROM area_admin WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    current_status = row['service_needed'] if row else 'No'

    # Toggle status
    new_status = 'No' if current_status == 'Yes' else 'Yes'

    # Update in DB
    if row:
        cursor.execute("UPDATE area_admin SET service_needed=? WHERE user_id=?", (new_status, user_id))
    else:
        cursor.execute("INSERT INTO area_admin (user_id, service_needed) VALUES (?, ?)", (user_id, new_status))
    
    conn.commit()
    return jsonify({"status": new_status})

    

# Route for admin to view & update service requests
@bp.route('/admin_service_requests', methods=['GET', 'POST'])
def admin_service_requests():
    if session.get('user_id') != 'admin':
        return redirect(url_for('app.login'))

    conn = create_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_status = request.form.get('service_status')

        cursor.execute("UPDATE Area_Admin SET service_status=? WHERE user_id=?", (new_status, user_id))
        conn.commit()
        return jsonify(success=True)

    # Fetch all service requests
    cursor.execute("SELECT * FROM Area_Admin")
    service_requests = cursor.fetchall()
    
    return render_template('admin_service_requests.html', service_requests=service_requests)

@bp.route('/update_admin_note', methods=['POST'])
def update_admin_note():
    data = request.get_json()
    user_id = data['user_id']
    admin_note = data['admin_note']

    # Update the admin note in the SQLite database
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE area_admin SET service_status = ? WHERE user_id = ?', (admin_note, user_id))
    conn.commit()
    
    return jsonify({"status": "success"})

# Get Billing Data
@bp.route('/get_billing_data')
def get_billing_data():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM billing")  # Table name should be lowercase if it is in DB
    bills = cursor.fetchall()

    conn.close()

    # Match column names correctly
    billing_data = []
    for bill in bills:
        billing_data.append({
            "Bill_id": bill[0],         # Matches `bill_id`
            "CID": bill[1],             # Matches `user_id`
            "Amount_Due": bill[2],      # Matches `amount_due`
            "Due_Date": bill[3],        # Matches `due_date`
            "Payment_Status": bill[4]   # Matches `payment_status`
        })

    return jsonify(billing_data)


# Add Bill
@bp.route('/add_bill', methods=['POST'])
def add_bill():
    if session.get('user_id') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    CID = data.get('CID')
    water_used = data.get('water_used')
    totalamt = data.get('totalamt')
    Payment_status = data.get('Payment_status')

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Billing (CID, water_used, totalamt, Payment_status) VALUES (?, ?, ?, ?)", 
                   (CID, water_used, totalamt, Payment_status))
    conn.commit()
    conn.close()

    return jsonify({"message": "Bill added successfully!"})

@bp.route("/add_new_bill", methods=["POST"])
def add_new_bill():
    data = request.json
    user_id = data.get("user_id")
    amount_due = data.get("amount_due")
    due_date = data.get("due_date")

    if not user_id or not amount_due or not due_date:
        return jsonify({"success": False, "error": "Invalid data"}), 400

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO billing (user_id, amount_due, due_date, payment_status) VALUES (?, ?, ?, 'Pending')",
                (user_id, amount_due, due_date))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# Delete Bill
@bp.route('/delete_bill/<int:bill_id>', methods=['POST'])
def delete_bill(bill_id):
    if session.get('user_id') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM Billing WHERE Bill_id=?", (bill_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Bill deleted successfully!"})


# Update Bill
@bp.route('/update_bill/<int:bill_id>', methods=['POST'])
def update_bill(bill_id):
    if session.get('user_id') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    water_used = data.get('water_used')
    totalamt = data.get('totalamt')
    Payment_status = data.get('Payment_status')

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE Billing SET water_used=?, totalamt=?, Payment_status=? WHERE Bill_id=?", 
                   (water_used, totalamt, Payment_status, bill_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Bill updated successfully!"})

@bp.route("/update_billing_status", methods=["POST"])
def update_billing_status():
    data = request.json
    bill_id = data.get("bill_id")
    new_status = data.get("payment_status")

    if not bill_id or not new_status:
        return jsonify({"success": False, "error": "Invalid data"}), 400

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("UPDATE billing SET payment_status = ? WHERE bill_id = ?", (new_status, bill_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

