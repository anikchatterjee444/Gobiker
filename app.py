from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = 'gobiker_secret_2024'

@app.teardown_appcontext
def teardown_db(e=None):
    from database import close_db
    close_db(e)

# ─── Auth Decorators ─────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Garage admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Public Routes ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    garages = db.execute('SELECT * FROM garages ORDER BY rating DESC LIMIT 6').fetchall()
    stats = {
        'users': db.execute('SELECT COUNT(*) FROM users WHERE role="user"').fetchone()[0],
        'garages': db.execute('SELECT COUNT(*) FROM garages').fetchone()[0],
        'services': db.execute('SELECT COUNT(*) FROM service_records').fetchone()[0],
    }
    return render_template('index.html', garages=garages, stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form.get('role', 'user')
        city = request.form.get('city', '').strip()
        phone = request.form.get('phone', '').strip()

        db = get_db()
        if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (name, email, password, role, city, phone) VALUES (?,?,?,?,?,?)',
            (name, email, hashed, role, city, phone)
        )
        db.commit()
        user_id = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()[0]

        if role == 'admin':
            garage_name = request.form.get('garage_name', name + "'s Garage")
            address = request.form.get('address', '')
            services = request.form.get('services', 'General Service, Oil Change, Tyre Service')
            db.execute(
                'INSERT INTO garages (owner_id, name, address, city, phone, services, rating) VALUES (?,?,?,?,?,?,?)',
                (user_id, garage_name, address, city, phone, services, 4.0)
            )
            db.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── User Routes ──────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def user_dashboard():
    db = get_db()
    uid = session['user_id']
    bikes = db.execute('SELECT * FROM bikes WHERE user_id=?', (uid,)).fetchall()
    # Recent service records across all user's bikes
    recent = db.execute('''
        SELECT sr.*, b.brand, b.model, g.name as garage_name
        FROM service_records sr
        JOIN bikes b ON sr.bike_id = b.id
        LEFT JOIN garages g ON sr.garage_id = g.id
        WHERE b.user_id=?
        ORDER BY sr.service_date DESC LIMIT 5
    ''', (uid,)).fetchall()

    reminders = []
    for bike in bikes:
        if bike['last_service_date']:
            last = datetime.strptime(bike['last_service_date'], '%Y-%m-%d')
            if datetime.now() - last > timedelta(days=90):
                reminders.append(f"{bike['brand']} {bike['model']} is due for service!")
        if bike['health_score'] and bike['health_score'] < 5:
            reminders.append(f"{bike['brand']} {bike['model']} has low health score ({bike['health_score']}/10)!")

    return render_template('user_dashboard.html', bikes=bikes, recent=recent, reminders=reminders)

@app.route('/bike/add', methods=['GET', 'POST'])
@login_required
def add_bike():
    if request.method == 'POST':
        db = get_db()
        db.execute('''
            INSERT INTO bikes (user_id, brand, model, year, reg_number, color, engine_cc, health_score)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (
            session['user_id'],
            request.form['brand'],
            request.form['model'],
            request.form['year'],
            request.form['reg_number'],
            request.form.get('color', ''),
            request.form.get('engine_cc', 0),
            7
        ))
        db.commit()
        flash('Bike added successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    return render_template('add_bike.html')

@app.route('/bike/<int:bike_id>')
@login_required
def bike_detail(bike_id):
    db = get_db()
    bike = db.execute('SELECT * FROM bikes WHERE id=? AND user_id=?', (bike_id, session['user_id'])).fetchone()
    if not bike:
        flash('Bike not found.', 'danger')
        return redirect(url_for('user_dashboard'))

    history = db.execute('''
        SELECT sr.*, g.name as garage_name
        FROM service_records sr
        LEFT JOIN garages g ON sr.garage_id = g.id
        WHERE sr.bike_id=?
        ORDER BY sr.service_date DESC
    ''', (bike_id,)).fetchall()

    fuel_logs = db.execute(
        'SELECT * FROM fuel_logs WHERE bike_id=? ORDER BY log_date DESC LIMIT 10', (bike_id,)
    ).fetchall()

    health_trend = db.execute('''
        SELECT health_score, service_date FROM service_records
        WHERE bike_id=? ORDER BY service_date ASC LIMIT 10
    ''', (bike_id,)).fetchall()

    return render_template('bike_detail.html', bike=bike, history=history, fuel_logs=fuel_logs, health_trend=health_trend)

@app.route('/bike/<int:bike_id>/fuel', methods=['POST'])
@login_required
def add_fuel_log(bike_id):
    db = get_db()
    db.execute('''
        INSERT INTO fuel_logs (bike_id, liters, cost_per_liter, total_cost, odometer, log_date)
        VALUES (?,?,?,?,?,?)
    ''', (
        bike_id,
        request.form['liters'],
        request.form['cost_per_liter'],
        float(request.form['liters']) * float(request.form['cost_per_liter']),
        request.form.get('odometer', 0),
        datetime.now().strftime('%Y-%m-%d')
    ))
    db.commit()
    flash('Fuel log added!', 'success')
    return redirect(url_for('bike_detail', bike_id=bike_id))

@app.route('/garages')
@login_required
def garages():
    db = get_db()
    city_filter = request.args.get('city', '')
    if city_filter:
        garages = db.execute('SELECT * FROM garages WHERE city LIKE ? ORDER BY rating DESC', (f'%{city_filter}%',)).fetchall()
    else:
        garages = db.execute('SELECT * FROM garages ORDER BY rating DESC').fetchall()
    cities = db.execute('SELECT DISTINCT city FROM garages ORDER BY city').fetchall()
    return render_template('garages.html', garages=garages, cities=cities, city_filter=city_filter)

@app.route('/garage/<int:garage_id>')
@login_required
def garage_detail(garage_id):
    db = get_db()
    garage = db.execute('SELECT g.*, u.name as owner_name FROM garages g JOIN users u ON g.owner_id=u.id WHERE g.id=?', (garage_id,)).fetchone()
    reviews = db.execute('''
        SELECT r.*, u.name as user_name FROM reviews r
        JOIN users u ON r.user_id=u.id
        WHERE r.garage_id=? ORDER BY r.review_date DESC
    ''', (garage_id,)).fetchall()
    user_reviewed = db.execute('SELECT id FROM reviews WHERE garage_id=? AND user_id=?', (garage_id, session['user_id'])).fetchone()
    return render_template('garage_detail.html', garage=garage, reviews=reviews, user_reviewed=user_reviewed)

@app.route('/garage/<int:garage_id>/review', methods=['POST'])
@login_required
def add_review(garage_id):
    db = get_db()
    existing = db.execute('SELECT id FROM reviews WHERE garage_id=? AND user_id=?', (garage_id, session['user_id'])).fetchone()
    if existing:
        flash('You have already reviewed this garage.', 'warning')
        return redirect(url_for('garage_detail', garage_id=garage_id))
    rating = int(request.form['rating'])
    comment = request.form['comment']
    db.execute(
        'INSERT INTO reviews (garage_id, user_id, rating, comment, review_date) VALUES (?,?,?,?,?)',
        (garage_id, session['user_id'], rating, comment, datetime.now().strftime('%Y-%m-%d'))
    )
    # Update garage avg rating
    avg = db.execute('SELECT AVG(rating) FROM reviews WHERE garage_id=?', (garage_id,)).fetchone()[0]
    db.execute('UPDATE garages SET rating=? WHERE id=?', (round(avg, 1), garage_id))
    db.commit()
    flash('Review submitted!', 'success')
    return redirect(url_for('garage_detail', garage_id=garage_id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        db.execute(
            'UPDATE users SET name=?, city=?, phone=? WHERE id=?',
            (request.form['name'], request.form['city'], request.form['phone'], uid)
        )
        db.commit()
        session['name'] = request.form['name']
        flash('Profile updated!', 'success')
    user = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    return render_template('profile.html', user=user)

# ─── Admin (Garage Owner) Routes ──────────────────────────────────────────────

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    uid = session['user_id']
    garage = db.execute('SELECT * FROM garages WHERE owner_id=?', (uid,)).fetchone()
    if not garage:
        flash('No garage found for your account.', 'danger')
        return redirect(url_for('index'))

    recent_services = db.execute('''
        SELECT sr.*, b.brand, b.model, b.reg_number, u.name as owner_name
        FROM service_records sr
        JOIN bikes b ON sr.bike_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE sr.garage_id=?
        ORDER BY sr.service_date DESC LIMIT 10
    ''', (garage['id'],)).fetchall()

    total_services = db.execute('SELECT COUNT(*) FROM service_records WHERE garage_id=?', (garage['id'],)).fetchone()[0]
    avg_health = db.execute('SELECT AVG(health_score) FROM service_records WHERE garage_id=?', (garage['id'],)).fetchone()[0]

    return render_template('admin_dashboard.html', garage=garage, recent_services=recent_services,
                           total_services=total_services, avg_health=avg_health)

@app.route('/admin/service/new', methods=['GET', 'POST'])
@admin_required
def new_service():
    db = get_db()
    uid = session['user_id']
    garage = db.execute('SELECT * FROM garages WHERE owner_id=?', (uid,)).fetchone()

    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip().upper()
        bike = db.execute('SELECT * FROM bikes WHERE UPPER(reg_number)=?', (reg_number,)).fetchone()
        if not bike:
            flash(f'No bike found with registration {reg_number}.', 'danger')
            return redirect(url_for('new_service'))

        health_score = int(request.form['health_score'])
        services_done = request.form['services_done']
        notes = request.form.get('notes', '')
        cost = request.form.get('cost', 0)
        odometer = request.form.get('odometer', 0)

        db.execute('''
            INSERT INTO service_records (bike_id, garage_id, health_score, services_done, notes, cost, odometer, service_date)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (bike['id'], garage['id'], health_score, services_done, notes, cost, odometer, datetime.now().strftime('%Y-%m-%d')))

        db.execute('''
            UPDATE bikes SET health_score=?, last_service_date=?, odometer=?
            WHERE id=?
        ''', (health_score, datetime.now().strftime('%Y-%m-%d'), odometer or bike['odometer'], bike['id']))

        db.commit()
        flash(f'Service record added for {bike["brand"]} {bike["model"]} ({reg_number})!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('new_service.html', garage=garage)

@app.route('/admin/garage/edit', methods=['GET', 'POST'])
@admin_required
def edit_garage():
    db = get_db()
    uid = session['user_id']
    garage = db.execute('SELECT * FROM garages WHERE owner_id=?', (uid,)).fetchone()
    if request.method == 'POST':
        db.execute('''
            UPDATE garages SET name=?, address=?, city=?, phone=?, services=?, open_hours=?
            WHERE owner_id=?
        ''', (
            request.form['name'],
            request.form['address'],
            request.form['city'],
            request.form['phone'],
            request.form['services'],
            request.form.get('open_hours', '9AM - 7PM'),
            uid
        ))
        db.commit()
        flash('Garage info updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_garage.html', garage=garage)

@app.route('/admin/lookup_bike')
@admin_required
def lookup_bike():
    reg = request.args.get('reg', '').strip().upper()
    if not reg:
        return jsonify({'found': False})
    db = get_db()
    bike = db.execute('SELECT b.*, u.name as owner_name, u.phone as owner_phone FROM bikes b JOIN users u ON b.user_id=u.id WHERE UPPER(b.reg_number)=?', (reg,)).fetchone()
    if bike:
        return jsonify({'found': True, 'brand': bike['brand'], 'model': bike['model'],
                        'year': bike['year'], 'owner': bike['owner_name'],
                        'phone': bike['owner_phone'], 'health': bike['health_score'],
                        'last_service': bike['last_service_date']})
    return jsonify({'found': False})

# ─── App Entry ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
