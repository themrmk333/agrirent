from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'agrirent_secret_key'

DB_NAME = 'agrirent.db'

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "@mr.mk333"


# 🔥 ADDED
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    );
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT NOT NULL,
        location TEXT NOT NULL,
        owner_id INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        equipment_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (equipment_id) REFERENCES equipment (id)
    );
    ''')
    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM equipment")
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
        ("Kubota MU5501", "Tractor", 2300, "kubota_mu5501.jpg", "Karnataka", 1)
    ]
    cur.executemany("INSERT INTO equipment (name, category, price, image, location, owner_id) VALUES (?, ?, ?, ?, ?, ?)", sample_equipment)
    
    admin_pass = generate_password_hash("admin")
    cur.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ("admin", admin_pass, 1))
        
    conn.commit()
    conn.close()

if not os.path.exists(DB_NAME):
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
        try:
            conn.execute('''INSERT INTO users (username, password, full_name, address, country, state, district, city, area, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (username, hashed, full_name, address, country, state, district, city, area, phone))
            conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type', 'user')
        username = request.form.get('username') or request.form.get('admin_email', '')
        password = request.form.get('password') or request.form.get('admin_password', '')
        
        if username == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user_id'] = 0
            session['username'] = "Admin"
            session['is_admin'] = 1
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
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
    # Recent bookings
    bookings = conn.execute('''SELECT b.id, e.id as equipment_id, e.name, b.date, b.status, e.price, e.image, b.end_date, b.damage_fee_paid, e.damage_charge 
        FROM bookings b JOIN equipment e ON b.equipment_id = e.id 
        WHERE b.user_id = ? ORDER BY b.id DESC LIMIT 10''', (session['user_id'],)).fetchall()
    
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    reminders = []
    for b in bookings:
        if b['status'] == 'Confirmed' and b['end_date'] == today_str:
            reminders.append(f"Today is your return date for {b['name']}. Please return the equipment. If you want to extend, please book again.")
            print(f"==========================================")
            print(f"REMINDER: {session['username']} - Today is the return date for {b['name']}!")
            print(f"==========================================")
    
    # Real Trending System
    # Detect which equipment category is booked the most
    trending_query = '''SELECT e.category, COUNT(b.id) as count
        FROM bookings b
        JOIN equipment e ON b.equipment_id = e.id
        GROUP BY e.category
        ORDER BY count DESC
        LIMIT 1'''
    trending_record = conn.execute(trending_query).fetchone()
    
    if trending_record:
        trending_cat = trending_record['category']
    else:
        trending_cat = get_trending_category() # fallback to seasonal logic
        
    trending_eq = conn.execute('SELECT * FROM equipment WHERE category = ? LIMIT 3', (trending_cat,)).fetchall()

    # Smart Recommendation System
    fav_cat_row = conn.execute('''SELECT e.category, COUNT(b.id) as count
        FROM bookings b JOIN equipment e ON b.equipment_id = e.id
        WHERE b.user_id = ? GROUP BY e.category ORDER BY count DESC LIMIT 1''', (session['user_id'],)).fetchone()
    
    if fav_cat_row:
        most_booked = fav_cat_row['category']
        if most_booked == 'Tractor':
            rec_query = 'SELECT * FROM equipment WHERE category IN ("Seeder", "Harvester") LIMIT 3'
        elif most_booked == 'Harvester':
            rec_query = 'SELECT * FROM equipment WHERE category = "Tractor" LIMIT 3'
        else:
            rec_query = 'SELECT * FROM equipment LIMIT 3'
        recommended_eq = conn.execute(rec_query).fetchall()
    else:
        recommended_eq = conn.execute('SELECT * FROM equipment ORDER BY RANDOM() LIMIT 3').fetchall()

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
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
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
    # 1. User Info
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        flash('User not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # 2. Rented Equipment History
    rented_history = conn.execute('''SELECT b.id, e.name, b.date, b.status, b.total_amount
        FROM bookings b
        JOIN equipment e ON b.equipment_id = e.id
        WHERE b.user_id = ?
        ORDER BY b.id DESC''', (user_id,)).fetchall()
    
    # 3. Listed Equipment
    listed_equipment = conn.execute('SELECT * FROM equipment WHERE owner_id = ?', (user_id,)).fetchall()
    
    # 4. Stats
    stats = {
        'total_bookings': len(rented_history),
        'total_spent': sum(b['total_amount'] or 0 for b in rented_history if b['status'] != 'Cancelled'),
        'total_listed': len(listed_equipment)
    }
    
    conn.close()
    return render_template('admin_user_detail.html', user=user, rented_history=rented_history, listed_equipment=listed_equipment, stats=stats)

@app.route('/equipment')
def equipment():
    # Anyone can browse freely without being logged in
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = 'SELECT * FROM equipment WHERE 1=1'
    params = []
    
    if search:
        query += ' AND name LIKE ?'
        params.append(f'%{search}%')
    if category:
        query += ' AND category = ?'
        params.append(category)
        
    conn = get_db()
    eq_list = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('equipment.html', equipment=eq_list, search=search, category=category)

# 🔥 UPDATED FUNCTION
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
        conn.execute('''INSERT INTO equipment (name, category, price, image, location, owner_id, quantity, damage_charge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
            (name, category, price, filename, location, session['user_id'], quantity, damage_charge))
        conn.commit()
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
    eq = conn.execute('SELECT * FROM equipment WHERE id = ?', (eq_id,)).fetchone()
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
    except:
        total_days = 1
        
    if total_days > 3:
        flash('Maximum booking allowed is 3 days only', 'error')
        return redirect(url_for('booking', eq_id=eq_id))
        
    if total_days < 1:
        flash('Invalid date range.', 'error')
        return redirect(url_for('booking', eq_id=eq_id))
    
    conn = get_db()
    
    eq = conn.execute('SELECT * FROM equipment WHERE id = ?', (eq_id,)).fetchone()
    if not eq:
        conn.close()
        flash('Equipment not found', 'error')
        return redirect(url_for('equipment'))
        
    if eq['quantity'] < 1:
        conn.close()
        flash('Sorry, this equipment is out of stock', 'error')
        return redirect(url_for('equipment'))
    
    overlap_count = conn.execute('''SELECT COUNT(*) FROM bookings 
        WHERE equipment_id = ? 
        AND status IN ('Confirmed', 'Damage Pending')
        AND start_date IS NOT NULL
        AND (start_date <= ? AND end_date >= ?)''', (eq_id, end_date, start_date)).fetchone()[0]
    
    if overlap_count >= eq['quantity']:
        flash('This equipment is fully booked for selected dates', 'error')
        conn.close()
        return redirect(url_for('booking', eq_id=eq_id))
        
    total_amount = float(eq['price']) * total_days
        
    session['pending_booking'] = {
        'equipment_id': eq_id,
        'start_date': start_date,
        'end_date': end_date,
        'phone_number': phone_number,
        'total_days': total_days,
        'total_amount': total_amount
    }
    
    conn.close()
    
    return render_template('payment.html', equipment=eq, start_date=start_date, end_date=end_date, total_days=total_days, total_amount=total_amount)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session or 'pending_booking' not in session:
        return redirect(url_for('login'))
        
    agreement = request.form.get('agreement')
    if not agreement:
        flash('Please accept agreement to continue', 'error')
        return redirect(url_for('dashboard'))
        
    booking_data = session.pop('pending_booking')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO bookings (user_id, equipment_id, date, status, start_date, end_date, phone_number, total_days, total_amount, agreement_accepted, damage_fee_paid)
        VALUES (?, ?, ?, 'Confirmed', ?, ?, ?, ?, ?, 1, 1)''', 
        (session['user_id'], booking_data['equipment_id'], booking_data['start_date'], booking_data['start_date'], booking_data['end_date'], booking_data['phone_number'], booking_data['total_days'], booking_data['total_amount']))
    booking_id = cur.lastrowid
    
    cur.execute('UPDATE equipment SET quantity = quantity - 1 WHERE id = ?', (booking_data['equipment_id'],))
    conn.commit()
    conn.close()
    
    flash('Payment successful! Booking confirmed.', 'success')
    return redirect(url_for('receipt', booking_id=booking_id))

@app.route('/receipt/<int:booking_id>')
def receipt(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    b = conn.execute(
        'SELECT b.*, e.name as equipment_name, e.price, u.username '
        'FROM bookings b '
        'JOIN equipment e ON b.equipment_id = e.id '
        'LEFT JOIN users u ON b.user_id = u.id '
        'WHERE b.id = ?', 
        (booking_id,)
    ).fetchone()
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
    b = conn.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    if b and b['status'] == 'Confirmed':
        if damage_status == 'damaged':
            conn.execute('UPDATE bookings SET status = "Damage Pending", damage_fee_paid = 0 WHERE id = ?', (booking_id,))
        else:
            conn.execute('UPDATE bookings SET status = "Returned" WHERE id = ?', (booking_id,))
            conn.execute('UPDATE equipment SET quantity = quantity + 1 WHERE id = ?', (b['equipment_id'],))
        conn.commit()
        flash('Return status updated.', 'success')
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/pay_damage/<int:booking_id>', methods=['POST'])
def pay_damage(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    b = conn.execute('SELECT * FROM bookings WHERE id = ? AND user_id = ?', (booking_id, session['user_id'])).fetchone()
    if b and b['status'] == 'Damage Pending':
        conn.execute('UPDATE bookings SET status = "Returned", damage_fee_paid = 1 WHERE id = ?', (booking_id,))
        conn.execute('UPDATE equipment SET quantity = quantity + 1 WHERE id = ?', (b['equipment_id'],))
        conn.commit()
        flash('Damage fee paid successfully. Equipment returned.', 'success')
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/api/location_equipment')
def location_equipment():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    conn = get_db()
    eq = conn.execute('SELECT * FROM equipment ORDER BY RANDOM() LIMIT 2').fetchall() 
    conn.close()
    
    import json
    return json.dumps([dict(ix) for ix in eq])

@app.route('/delete_equipment/<int:eq_id>', methods=['POST'])
def delete_equipment(eq_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    eq = conn.execute('SELECT * FROM equipment WHERE id = ?', (eq_id,)).fetchone()
    if eq and (int(session.get('is_admin', 0)) == 1 or eq['owner_id'] == session['user_id']):
        conn.execute('DELETE FROM equipment WHERE id = ?', (eq_id,))
        conn.commit()
        flash('Equipment deleted successfully.', 'success')
    else:
        flash('Unauthorized action', 'error')
    conn.close()
    return redirect(request.referrer or url_for('equipment'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or int(session.get('is_admin', 0)) != 1:
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Prevent admin from deleting themselves
    if user_id == session.get('user_id'):
        flash('You cannot delete your own admin account!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db()
    try:
        # OPTION A: Keep historical bookings but mark user as deleted
        # Note: user_id is NOT NULL, so we assign to admin (id 0) or update status
        conn.execute('UPDATE bookings SET status = "Deleted User" WHERE user_id = ?', (user_id,))
        
        # Handle equipment listed by the user (assign to admin or remove)
        conn.execute('UPDATE equipment SET owner_id = 1 WHERE owner_id = ?', (user_id,)) # 1 is usually the database admin
        
        # Finally delete the user
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    b = conn.execute('SELECT * FROM bookings WHERE id = ? AND user_id = ?', (booking_id, session['user_id'])).fetchone()
    if b and b['status'] == 'Confirmed':
        conn.execute('UPDATE bookings SET status = ? WHERE id = ?', ('Cancelled', booking_id))
        conn.execute('UPDATE equipment SET quantity = quantity + 1 WHERE id = ?', (b['equipment_id'],))
        conn.commit()
    conn.close()
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or int(session.get('is_admin', 0)) != 1:
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))
        
    conn = get_db()
    
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_eq = conn.execute('SELECT COUNT(*) FROM equipment').fetchone()[0]
    total_bookings = conn.execute('SELECT COUNT(*) FROM bookings WHERE status="Confirmed"').fetchone()[0]
    cancelled_bookings = conn.execute('SELECT COUNT(*) FROM bookings WHERE status="Cancelled"').fetchone()[0]
    
    all_users = conn.execute('SELECT id, username, full_name, phone, city FROM users').fetchall()
    
    tp_row = conn.execute(
        'SELECT SUM(e.price) as total_profit '
        'FROM bookings b '
        'JOIN equipment e ON b.equipment_id = e.id '
        'WHERE b.status="Confirmed"'
    ).fetchone()
    total_profit = tp_row['total_profit'] if tp_row and tp_row['total_profit'] else 0
    
    all_bookings_detail = conn.execute(
        'SELECT b.id, u.username, e.name as equipment_name, b.date, b.status, e.price '
        'FROM bookings b '
        'LEFT JOIN users u ON b.user_id = u.id '
        'JOIN equipment e ON b.equipment_id = e.id '
        'ORDER BY b.id DESC'
    ).fetchall()
    
    all_eq_detail = conn.execute(
        'SELECT e.id, e.name, e.category, e.price, u.username as owner_name, e.owner_id '
        'FROM equipment e '
        'LEFT JOIN users u ON e.owner_id = u.id '
        'ORDER BY e.id DESC'
    ).fetchall()

    # Graphical Data
    # 1. Monthly Bookings:
    mb_rows = conn.execute('''SELECT strftime('%m', date) as month, COUNT(*) as cnt
        FROM bookings
        GROUP BY month''').fetchall()
    mb_dict = {str(i).zfill(2): 0 for i in range(1, 13)}
    for row in mb_rows:
        if row['month']:
            mb_dict[row['month']] = row['cnt']
            
    # 2. Monthly Profit:
    mp_rows = conn.execute('''SELECT strftime('%m', b.date) as month, SUM(e.price) as profit
        FROM bookings b
        JOIN equipment e ON b.equipment_id = e.id
        WHERE b.status='Confirmed'
        GROUP BY month''').fetchall()
    mp_dict = {str(i).zfill(2): 0 for i in range(1, 13)}
    for row in mp_rows:
        if row['month']:
            mp_dict[row['month']] = row['profit']

    # 3. Most Used:
    mr_rows = conn.execute('''SELECT e.name, COUNT(b.id) as cnt
        FROM equipment e
        LEFT JOIN bookings b ON e.id = b.equipment_id
        GROUP BY e.id
        ORDER BY cnt DESC
        LIMIT 5''').fetchall()
    
    mr_labels = [row['name'] for row in mr_rows]
    mr_data = [row['cnt'] for row in mr_rows]
    
    m_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_data = [mb_dict[str(i).zfill(2)] for i in range(1, 13)]
    m_profit = [mp_dict[str(i).zfill(2)] for i in range(1, 13)]
    
    # 4. Weekly Data:
    w_rows = conn.execute('''SELECT strftime('%W', date) as week, COUNT(*) as cnt, SUM(total_amount) as profit
        FROM bookings
        WHERE status IN ('Confirmed', 'Returned')
        GROUP BY week
        ORDER BY week DESC
        LIMIT 5''').fetchall()
    
    # Reverse so oldest is first within the 5 point window
    w_rows.reverse()
    w_labels = [row['week'] for row in w_rows]
    w_data = [row['cnt'] for row in w_rows]
    w_profit = [row['profit'] if row['profit'] else 0 for row in w_rows]
    
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

if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
        seed_db()
        
    # Execute structural migration safely
    try:
        conn = sqlite3.connect(DB_NAME)
        columns = [
            ('equipment', 'quantity', 'INTEGER DEFAULT 1'),
            ('equipment', 'damage_charge', 'REAL DEFAULT 500.0'),
            ('bookings', 'start_date', 'TEXT'),
            ('bookings', 'end_date', 'TEXT'),
            ('bookings', 'phone_number', 'TEXT'),
            ('bookings', 'total_days', 'INTEGER DEFAULT 1'),
            ('bookings', 'total_amount', 'REAL DEFAULT 0.0'),
            ('bookings', 'agreement_accepted', 'INTEGER DEFAULT 0'),
            ('bookings', 'damage_fee_paid', 'INTEGER DEFAULT 1'),
            ('users', 'full_name', 'TEXT'),
            ('users', 'address', 'TEXT'),
            ('users', 'country', 'TEXT'),
            ('users', 'state', 'TEXT'),
            ('users', 'district', 'TEXT'),
            ('users', 'city', 'TEXT'),
            ('users', 'area', 'TEXT'),
            ('users', 'phone', 'TEXT'),
        ]
        for tbl, col, dtype in columns:
            try:
                conn.execute(f'ALTER TABLE {tbl} ADD COLUMN {col} {dtype};')
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        pass
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)