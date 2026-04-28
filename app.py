from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
import datetime
import os
import random
import time
import razorpay
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'agrirent_secret_key'

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql://agrirent_db_l8fu_user:6xMbksbAC1SYEVlhoLDumN920SoZyodB@dpg-d7jov4jeo5us73adu7b0-a.oregon-postgres.render.com/agrirent_db_l8fu"

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "@mr.mk333"

# 🔥 ADDED
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_uG6vS7n3H5kR6m')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'test_secret')
razor_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def get_db():
    return psycopg2.connect(DATABASE_URL)

def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        full_name TEXT,
        address TEXT,
        country TEXT,
        state TEXT,
        district TEXT,
        city TEXT,
        area TEXT,
        phone TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS equipment (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT NOT NULL,
        location TEXT NOT NULL,
        owner_id INTEGER DEFAULT 0,
        quantity INTEGER DEFAULT 1,
        damage_charge REAL DEFAULT 500.0
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        equipment_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT,
        phone_number TEXT,
        total_days INTEGER DEFAULT 1,
        total_amount REAL DEFAULT 0.0,
        refund_amount REAL DEFAULT 0.0,
        agreement_accepted INTEGER DEFAULT 0,
        damage_fee_paid INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (equipment_id) REFERENCES equipment (id)
    )
    ''')
    conn.commit()
    cur.close()
    conn.close()


def seed_db():
    conn = get_db()
    cur = get_cursor(conn)

    # Only seed if equipment table is empty
    cur.execute("SELECT COUNT(*) AS count FROM equipment")
    row = cur.fetchone()
    if row['count'] == 0:
        sample_equipment = [
            ("Mahindra 575 DI", "Tractor", 1500, "mahindra_575.jpg", "Maharashtra", 1),
            ("Mahindra 475 DI", "Tractor", 1400, "mahindra_475.jpg", "Maharashtra", 1),
            ("Mahindra Arjun 555", "Tractor", 1800, "mahindra_arjun_555.jpg", "Maharashtra", 1),
            ("Swaraj 735 FE", "Tractor", 1300, "swaraj_735.jpg", "Punjab", 1),
            ("Swaraj 744 FE", "Tractor", 1500, "swaraj_744.jpg", "Punjab", 1),
            ("John Deere 5050D", "Tractor", 2000, "john_5050.jpg", "Haryana", 1),
            ("John Deere 5310", "Tractor", 2200, "john_5310.jpg", "Haryana", 1),
            ("New Holland 3630", "Tractor", 2100, "newholland_3630.jpg", "UP", 1),
            ("New Holland 3600", "Tractor", 1900, "newholland_3600.jpg", "UP", 1),
            ("Massey Ferguson 1035", "Tractor", 1600, "massey_1035.jpg", "Rajasthan", 1),
            ("Massey Ferguson 241", "Tractor", 1700, "massey_241.jpg", "Rajasthan", 1),
            ("Sonalika DI 745", "Tractor", 1500, "sonalika_745.jpg", "Bihar", 1),
            ("Sonalika DI 750", "Tractor", 1600, "sonalika_750.jpg", "Bihar", 1),
            ("Eicher 380", "Tractor", 1400, "eicher_380.jpg", "MP", 1),
            ("Kubota MU5501", "Tractor", 2300, "kubota_mu5501.jpg", "Karnataka", 1),
        ]
        cur.executemany(
            "INSERT INTO equipment (name, category, price, image, location, owner_id) VALUES (%s, %s, %s, %s, %s, %s)",
            sample_equipment
        )

    # Only seed admin user if users table is empty
    cur.execute("SELECT COUNT(*) AS count FROM users")
    row = cur.fetchone()
    if row['count'] == 0:
        admin_pass = generate_password_hash("admin")
        cur.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
            ("admin", admin_pass, 1)
        )

    conn.commit()
    cur.close()
    conn.close()


# Initialize DB tables and seed on startup
init_db()
seed_db()


def get_trending_category():
    month = datetime.datetime.now().month
    if 3 <= month <= 6:
        return "Tractor"
    elif 7 <= month <= 10:
        return "Seeder"
    else:
        return "Harvester"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        address = request.form['address']
        country = request.form['country']
        state = request.form['state']
        district = request.form['district']
        city = request.form['city']
        area = request.form['area']
        phone = request.form['phone']

        if len(phone) != 10:
            flash('Phone number must be exactly 10 digits.', 'error')
            return render_template('register.html')

        hashed = generate_password_hash(password)

        conn = get_db()
        cur = get_cursor(conn)
        try:
            cur.execute(
                '''INSERT INTO users (username, password, full_name, address, country, state, district, city, area, phone)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (username, hashed, full_name, address, country, state, district, city, area, phone)
            )
            conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            err_str = str(e).lower() + repr(e).lower()
            if 'unique' in err_str or 'violation' in err_str:
                flash('Username already exists.', 'error')
            else:
                flash('An error occurred during registration.', 'error')
        finally:
            cur.close()
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username') or request.form.get('admin_email', '')
        password = request.form.get('password') or request.form.get('admin_password', '')

        if username == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user_id'] = 0
            session['username'] = "Admin"
            session['is_admin'] = 1
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        conn = get_db()
        cur = get_cursor(conn)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name'] or user['username']
            session['is_admin'] = user['is_admin']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)

    # Recent bookings
    cur.execute('''SELECT b.id, e.id as equipment_id, e.name, b.date, b.status, e.price, e.image, b.end_date, b.damage_fee_paid, e.damage_charge
        FROM bookings b JOIN equipment e ON b.equipment_id = e.id
        WHERE b.user_id = %s ORDER BY b.id DESC LIMIT 10''', (session['user_id'],))
    bookings = cur.fetchall()

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    reminders = []
    for b in bookings:
        if b['status'] == 'Confirmed' and b['end_date'] == today_str:
            reminders.append(f"Today is your return date for {b['name']}. Please return the equipment. If you want to extend, please book again.")
            print(f"==========================================")
            print(f"REMINDER: {session['username']} - Today is the return date for {b['name']}!")
            print(f"==========================================")

    # Real Trending System
    cur.execute('''SELECT e.category, COUNT(b.id) as count
        FROM bookings b
        JOIN equipment e ON b.equipment_id = e.id
        GROUP BY e.category
        ORDER BY count DESC
        LIMIT 1''')
    trending_record = cur.fetchone()

    if trending_record:
        trending_cat = trending_record['category']
    else:
        trending_cat = get_trending_category()

    cur.execute('SELECT * FROM equipment WHERE category = %s LIMIT 3', (trending_cat,))
    trending_eq = cur.fetchall()

    # Smart Recommendation System
    cur.execute('''SELECT e.category, COUNT(b.id) as count
        FROM bookings b JOIN equipment e ON b.equipment_id = e.id
        WHERE b.user_id = %s GROUP BY e.category ORDER BY count DESC LIMIT 1''', (session['user_id'],))
    fav_cat_row = cur.fetchone()

    if fav_cat_row:
        most_booked = fav_cat_row['category']
        if most_booked == 'Tractor':
            cur.execute("SELECT * FROM equipment WHERE category IN ('Seeder', 'Harvester') LIMIT 3")
        elif most_booked == 'Harvester':
            cur.execute("SELECT * FROM equipment WHERE category = 'Tractor' LIMIT 3")
        else:
            cur.execute('SELECT * FROM equipment LIMIT 3')
        recommended_eq = cur.fetchall()
    else:
        cur.execute('SELECT * FROM equipment ORDER BY RANDOM() LIMIT 3')
        recommended_eq = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('dashboard.html',
                           bookings=bookings,
                           trending_eq=trending_eq,
                           trending_cat=trending_cat,
                           recommended_eq=recommended_eq,
                           reminders=reminders,
                           full_name=session.get('full_name', 'User'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        flash('User profile not found.', 'error')
        return redirect(url_for('index'))

    return render_template('profile.html', user=user)


@app.route('/admin/user_detail/<int:user_id>')
def admin_user_detail(user_id):
    if 'user_id' not in session or int(session.get('is_admin', 0)) != 1:
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db()
    cur = get_cursor(conn)

    # 1. User Info
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        flash('User not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    # 2. Rented Equipment History
    cur.execute('''SELECT b.id, e.name, b.date, b.status, b.total_amount
        FROM bookings b
        JOIN equipment e ON b.equipment_id = e.id
        WHERE b.user_id = %s
        ORDER BY b.id DESC''', (user_id,))
    rented_history = cur.fetchall()

    # 3. Listed Equipment
    cur.execute('SELECT * FROM equipment WHERE owner_id = %s', (user_id,))
    listed_equipment = cur.fetchall()

    # 4. Stats
    stats = {
        'total_bookings': len(rented_history),
        'total_spent': sum(b['total_amount'] or 0 for b in rented_history if b['status'] != 'Cancelled'),
        'total_listed': len(listed_equipment)
    }

    cur.close()
    conn.close()
    return render_template('admin_user_detail.html', user=user, rented_history=rented_history, listed_equipment=listed_equipment, stats=stats)


@app.route('/equipment')
def equipment():
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    query = 'SELECT * FROM equipment WHERE 1=1'
    params = []

    if search:
        query += ' AND name LIKE %s'
        params.append(f'%{search}%')
    if category:
        query += ' AND category = %s'
        params.append(category)

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(query, params)
    eq_list = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('equipment.html', equipment=eq_list, search=search, category=category)


@app.route('/add_equipment', methods=['GET', 'POST'])
def add_equipment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        location = request.form['location']
        quantity = request.form.get('quantity', 1)
        damage_charge = request.form.get('damage_charge', 500)

        image_file = request.files['image']
        filename = ""

        if image_file:
            filename = image_file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO equipment (name, category, price, image, location, owner_id, quantity, damage_charge)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (name, category, price, filename, location, session['user_id'], quantity, damage_charge)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash('Equipment added successfully!', 'success')
        return redirect(url_for('equipment'))

    return render_template('add_equipment.html')


@app.route('/booking/<int:eq_id>', methods=['GET'])
def booking(eq_id):
    if 'user_id' not in session:
        flash('Login required to rent equipment. Please login or register to continue booking', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM equipment WHERE id = %s', (eq_id,))
    eq = cur.fetchone()
    cur.close()
    conn.close()

    if not eq:
        flash('Equipment not found', 'error')
        return redirect(url_for('equipment'))

    return render_template('booking.html', equipment=eq)


@app.route('/payment', methods=['POST'])
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    eq_id = request.form['equipment_id']
    start_date = request.form.get('start_date', request.form.get('date', ''))
    end_date = request.form.get('end_date', request.form.get('date', ''))
    phone_number = request.form.get('phone_number', '')

    if not phone_number or len(phone_number) != 10:
        flash('Valid 10-digit phone number is required.', 'error')
        return redirect(url_for('booking', eq_id=eq_id))

    try:
        start_d = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_d = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        total_days = (end_d - start_d).days + 1
    except Exception:
        total_days = 1

    if total_days > 3:
        flash('Maximum booking allowed is 3 days only', 'error')
        return redirect(url_for('booking', eq_id=eq_id))

    if total_days < 1:
        flash('Invalid date range.', 'error')
        return redirect(url_for('booking', eq_id=eq_id))

    conn = get_db()
    cur = get_cursor(conn)

    cur.execute('SELECT * FROM equipment WHERE id = %s', (eq_id,))
    eq = cur.fetchone()
    if not eq:
        cur.close()
        conn.close()
        flash('Equipment not found', 'error')
        return redirect(url_for('equipment'))

    if eq['quantity'] < 1:
        cur.close()
        conn.close()
        flash('Sorry, this equipment is out of stock', 'error')
        return redirect(url_for('equipment'))

    cur.execute('''SELECT COUNT(*) AS count FROM bookings
        WHERE equipment_id = %s
        AND status IN ('Confirmed', 'Damage Pending')
        AND start_date IS NOT NULL
        AND (start_date <= %s AND end_date >= %s)''', (eq_id, end_date, start_date))
    row = cur.fetchone()
    overlap_count = row['count'] if row else 0

    if overlap_count >= eq['quantity']:
        flash('This equipment is fully booked for selected dates', 'error')
        cur.close()
        conn.close()
        return redirect(url_for('booking', eq_id=eq_id))

    total_amount = float(eq['price']) * total_days

    # Razorpay Order Creation
    data = {
        "amount": int(total_amount * 100), # Amount in paise
        "currency": "INR",
        "receipt": f"receipt_{int(time.time())}",
        "payment_capture": 1
    }
    
    try:
        order = razor_client.order.create(data=data)
        razorpay_order_id = order['id']
    except Exception as e:
        flash(f"Payment gateway error: {str(e)}", 'error')
        cur.close()
        conn.close()
        return redirect(url_for('booking', eq_id=eq_id))

    session['pending_booking'] = {
        'equipment_id': eq_id,
        'start_date': start_date,
        'end_date': end_date,
        'phone_number': phone_number,
        'total_days': total_days,
        'total_amount': total_amount,
        'razorpay_order_id': razorpay_order_id
    }

    cur.close()
    conn.close()

    return render_template('payment.html', 
                           equipment=eq, 
                           start_date=start_date, 
                           end_date=end_date, 
                           total_days=total_days, 
                           total_amount=total_amount,
                           phone_number=phone_number,
                           razorpay_order_id=razorpay_order_id,
                           razorpay_key_id=RAZORPAY_KEY_ID)

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    if 'user_id' not in session or 'pending_booking' not in session:
        return redirect(url_for('login'))

    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')

    params_dict = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }

    try:
        # Verify Razorpay signature
        razor_client.utility.verify_payment_signature(params_dict)
        
        # If verification successful, finalize booking
        booking_data = session.pop('pending_booking')
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO bookings (user_id, equipment_id, date, status, start_date, end_date, phone_number, total_days, total_amount, agreement_accepted, damage_fee_paid)
               VALUES (%s, %s, %s, 'Confirmed', %s, %s, %s, %s, %s, 1, 1) RETURNING id''',
            (session['user_id'], booking_data['equipment_id'], booking_data['start_date'],
             booking_data['start_date'], booking_data['end_date'], booking_data['phone_number'],
             booking_data['total_days'], booking_data['total_amount'])
        )
        booking_id = cur.fetchone()[0]

        cur.execute('UPDATE equipment SET quantity = quantity - 1 WHERE id = %s', (booking_data['equipment_id'],))
        conn.commit()
        cur.close()
        conn.close()

        flash('Payment successful! Booking confirmed.', 'success')
        return redirect(url_for('receipt', booking_id=booking_id))

    except razorpay.errors.SignatureVerificationError:
        flash('Payment verification failed. Security breach detected.', 'error')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/receipt/<int:booking_id>')
def receipt(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(
        'SELECT b.*, e.name as equipment_name, e.price, u.username '
        'FROM bookings b '
        'JOIN equipment e ON b.equipment_id = e.id '
        'LEFT JOIN users u ON b.user_id = u.id '
        'WHERE b.id = %s',
        (booking_id,)
    )
    b = cur.fetchone()
    cur.close()
    conn.close()

    if not b:
        flash('Receipt not found.', 'error')
        return redirect(url_for('dashboard'))

    if b['user_id'] != session['user_id'] and session.get('is_admin') != 1:
        flash('Unauthorized.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('receipt.html', booking=b)


@app.route('/admin_return/<int:booking_id>', methods=['POST'])
def admin_return(booking_id):
    if session.get('is_admin') != 1:
        return redirect(url_for('login'))

    damage_status = request.form.get('damage_status')
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
    b = cur.fetchone()
    if b and b['status'] == 'Confirmed':
        if damage_status == 'damaged':
            cur.execute("UPDATE bookings SET status = 'Damage Pending', damage_fee_paid = 0 WHERE id = %s", (booking_id,))
        else:
            cur.execute("UPDATE bookings SET status = 'Returned' WHERE id = %s", (booking_id,))
            cur.execute('UPDATE equipment SET quantity = quantity + 1 WHERE id = %s', (b['equipment_id'],))
        conn.commit()
        flash('Return status updated.', 'success')
    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/pay_damage/<int:booking_id>', methods=['POST'])
def pay_damage(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM bookings WHERE id = %s AND user_id = %s', (booking_id, session['user_id']))
    b = cur.fetchone()
    if b and b['status'] == 'Damage Pending':
        cur.execute("UPDATE bookings SET status = 'Returned', damage_fee_paid = 1 WHERE id = %s", (booking_id,))
        cur.execute('UPDATE equipment SET quantity = quantity + 1 WHERE id = %s', (b['equipment_id'],))
        conn.commit()
        flash('Damage fee paid successfully. Equipment returned.', 'success')
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/api/location_equipment')
def location_equipment():
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM equipment ORDER BY RANDOM() LIMIT 2')
    eq = cur.fetchall()
    cur.close()
    conn.close()

    import json
    return json.dumps([dict(ix) for ix in eq])


@app.route('/delete_equipment/<int:eq_id>', methods=['POST'])
def delete_equipment(eq_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM equipment WHERE id = %s', (eq_id,))
    eq = cur.fetchone()
    if eq and (int(session.get('is_admin', 0)) == 1 or eq['owner_id'] == session['user_id']):
        cur.execute('DELETE FROM equipment WHERE id = %s', (eq_id,))
        conn.commit()
        flash('Equipment deleted successfully.', 'success')
    else:
        flash('Unauthorized action', 'error')
    cur.close()
    conn.close()
    return redirect(request.referrer or url_for('equipment'))


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or int(session.get('is_admin', 0)) != 1:
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))

    if user_id == session.get('user_id'):
        flash('You cannot delete your own admin account!', 'error')
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE bookings SET status = 'Deleted User' WHERE user_id = %s", (user_id,))
        cur.execute('UPDATE equipment SET owner_id = 1 WHERE owner_id = %s', (user_id,))
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = get_cursor(conn)
    
    # Securely fetch booking - only if it belongs to the user
    cur.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
    b = cur.fetchone()
    
    if not b:
        flash('Booking not found.', 'error')
    elif b['user_id'] != session['user_id']:
        # Security: Prevent unauthorized cancellation
        flash('Unauthorized action.', 'error')
    elif b['status'] == 'Cancelled':
        # Prevent double cancellation
        flash('Booking already cancelled.', 'info')
    elif b['status'] != 'Confirmed':
        flash('This booking cannot be cancelled at its current status.', 'error')
    else:
        # Proceed with cancellation
        total = b['total_amount'] or 0
        # Accurate 20% deduction (80% refund) with rounding
        refund = round(float(total) * 0.80, 2)
        
        cur.execute("UPDATE bookings SET status = 'Cancelled', refund_amount = %s WHERE id = %s", (refund, booking_id))
        cur.execute('UPDATE equipment SET quantity = quantity + 1 WHERE id = %s', (b['equipment_id'],))
        conn.commit()
        
        # Professional dynamic feedback
        flash(f'Booking cancelled. ₹{refund:,.2f} refunded after 20% deduction.', 'success')
        
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or int(session.get('is_admin', 0)) != 1:
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db()
    cur = get_cursor(conn)

    cur.execute('SELECT COUNT(*) AS count FROM users')
    row = cur.fetchone()
    total_users = row['count'] if row else 0

    cur.execute('SELECT COUNT(*) AS count FROM equipment')
    row = cur.fetchone()
    total_eq = row['count'] if row else 0

    cur.execute("SELECT COUNT(*) AS count FROM bookings WHERE status = 'Confirmed'")
    row = cur.fetchone()
    total_bookings = row['count'] if row else 0

    cur.execute("SELECT COUNT(*) AS count FROM bookings WHERE status = 'Cancelled'")
    row = cur.fetchone()
    cancelled_bookings = row['count'] if row else 0

    cur.execute('SELECT id, username, full_name, phone, city FROM users')
    all_users = cur.fetchall()

    cur.execute(
        "SELECT SUM(e.price) as total_profit "
        "FROM bookings b "
        "JOIN equipment e ON b.equipment_id = e.id "
        "WHERE b.status = 'Confirmed'"
    )
    tp_row = cur.fetchone()
    total_profit = tp_row['total_profit'] if tp_row and tp_row['total_profit'] else 0

    cur.execute(
        'SELECT b.id, u.username, e.name as equipment_name, b.date, b.status, e.price '
        'FROM bookings b '
        'LEFT JOIN users u ON b.user_id = u.id '
        'JOIN equipment e ON b.equipment_id = e.id '
        'ORDER BY b.id DESC'
    )
    all_bookings_detail = cur.fetchall()

    cur.execute(
        'SELECT e.id, e.name, e.category, e.price, u.username as owner_name, e.owner_id '
        'FROM equipment e '
        'LEFT JOIN users u ON e.owner_id = u.id '
        'ORDER BY e.id DESC'
    )
    all_eq_detail = cur.fetchall()

    # Graphical Data
    # 1. Monthly Bookings (PostgreSQL: EXTRACT or TO_CHAR)
    cur.execute("""SELECT TO_CHAR(TO_DATE(date, 'YYYY-MM-DD'), 'MM') as month, COUNT(*) as cnt
        FROM bookings
        WHERE date IS NOT NULL AND date != ''
        GROUP BY month""")
    mb_rows = cur.fetchall()
    mb_dict = {str(i).zfill(2): 0 for i in range(1, 13)}
    for row in mb_rows:
        if row['month']:
            mb_dict[row['month']] = row['cnt']

    # 2. Monthly Profit
    cur.execute("""SELECT TO_CHAR(TO_DATE(b.date, 'YYYY-MM-DD'), 'MM') as month, SUM(e.price) as profit
        FROM bookings b
        JOIN equipment e ON b.equipment_id = e.id
        WHERE b.status = 'Confirmed' AND b.date IS NOT NULL AND b.date != ''
        GROUP BY month""")
    mp_rows = cur.fetchall()
    mp_dict = {str(i).zfill(2): 0 for i in range(1, 13)}
    for row in mp_rows:
        if row['month']:
            mp_dict[row['month']] = row['profit']

    # 3. Most Used Equipment
    cur.execute("""SELECT e.name, COUNT(b.id) as cnt
        FROM equipment e
        LEFT JOIN bookings b ON e.id = b.equipment_id
        GROUP BY e.id, e.name
        ORDER BY cnt DESC
        LIMIT 5""")
    mr_rows = cur.fetchall()
    mr_labels = [row['name'] for row in mr_rows]
    mr_data = [row['cnt'] for row in mr_rows]

    m_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_data = [mb_dict[str(i).zfill(2)] for i in range(1, 13)]
    m_profit = [mp_dict[str(i).zfill(2)] for i in range(1, 13)]

    # 4. Weekly Data
    cur.execute("""SELECT TO_CHAR(TO_DATE(date, 'YYYY-MM-DD'), 'IW') as week, COUNT(*) as cnt, SUM(total_amount) as profit
        FROM bookings
        WHERE status IN ('Confirmed', 'Returned') AND date IS NOT NULL AND date != ''
        GROUP BY week
        ORDER BY week DESC
        LIMIT 5""")
    w_rows = cur.fetchall()
    w_rows = list(reversed(w_rows))
    w_labels = [row['week'] for row in w_rows]
    w_data = [row['cnt'] for row in w_rows]
    w_profit = [row['profit'] if row['profit'] else 0 for row in w_rows]

    cur.close()
    conn.close()

    return render_template('admin_dashboard.html',
        total_users=total_users,
        total_eq=total_eq,
        total_bookings=total_bookings,
        cancelled_bookings=cancelled_bookings,
        total_profit=total_profit,
        all_users=all_users,
        all_bookings=all_bookings_detail,
        all_eq=all_eq_detail,
        mr_labels=mr_labels, mr_data=mr_data,
        m_labels=m_labels, m_data=m_data, m_profit=m_profit,
        w_labels=w_labels, w_data=w_data, w_profit=w_profit
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)