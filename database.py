import sqlite3
import os
from flask import g
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

DATABASE = os.path.join(os.path.dirname(__file__), 'gobiker.db')

def get_db():
    from app import app
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    from app import app
    with app.app_context():
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')

        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT "user",
                city TEXT DEFAULT "",
                phone TEXT DEFAULT "",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS garages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                address TEXT DEFAULT "",
                city TEXT DEFAULT "",
                phone TEXT DEFAULT "",
                services TEXT DEFAULT "General Service, Oil Change",
                open_hours TEXT DEFAULT "9AM - 7PM",
                rating REAL DEFAULT 4.0,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS bikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER DEFAULT 2020,
                reg_number TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT "",
                engine_cc INTEGER DEFAULT 150,
                health_score INTEGER DEFAULT 7,
                odometer INTEGER DEFAULT 0,
                last_service_date TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS service_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bike_id INTEGER NOT NULL,
                garage_id INTEGER,
                health_score INTEGER NOT NULL,
                services_done TEXT DEFAULT "",
                notes TEXT DEFAULT "",
                cost REAL DEFAULT 0,
                odometer INTEGER DEFAULT 0,
                service_date TEXT NOT NULL,
                FOREIGN KEY(bike_id) REFERENCES bikes(id),
                FOREIGN KEY(garage_id) REFERENCES garages(id)
            );

            CREATE TABLE IF NOT EXISTS fuel_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bike_id INTEGER NOT NULL,
                liters REAL NOT NULL,
                cost_per_liter REAL DEFAULT 0,
                total_cost REAL DEFAULT 0,
                odometer INTEGER DEFAULT 0,
                log_date TEXT NOT NULL,
                FOREIGN KEY(bike_id) REFERENCES bikes(id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                garage_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT DEFAULT "",
                review_date TEXT NOT NULL,
                FOREIGN KEY(garage_id) REFERENCES garages(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        ''')
        db.commit()

        # Seed demo data if empty
        count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if count == 0:
            _seed_demo(db)

        db.close()

def _seed_demo(db):
    cities = ['Bengaluru', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai', 'Pune']
    garage_data = [
        ('Rajesh Moto Works', 'MG Road, Bengaluru', 'Bengaluru', '9876543210',
         'Engine Overhaul, Oil Change, Brake Service, Tyre Change, Chain Lubrication', '8AM - 8PM', 4.7),
        ('SpeedBike Garage', 'Andheri West, Mumbai', 'Mumbai', '9123456789',
         'General Service, Carburetor Cleaning, Battery Replacement, Suspension Check', '9AM - 7PM', 4.5),
        ('Two Wheel Tech', 'Koramangala, Bengaluru', 'Bengaluru', '9988776655',
         'Full Service, Electrical Repair, Body Work, Disc Brake Service', '8:30AM - 7:30PM', 4.3),
        ('Hyder Bike Hub', 'Banjara Hills, Hyderabad', 'Hyderabad', '9871234567',
         'Oil Change, Tyre Balancing, Engine Tune-up, Clutch Repair', '9AM - 6PM', 4.6),
        ('Chennai Cycles Pro', 'Anna Nagar, Chennai', 'Chennai', '9445566778',
         'General Service, Chain Service, Air Filter, Spark Plug', '8AM - 7PM', 4.2),
        ('PuneWheelers', 'Kothrud, Pune', 'Pune', '9665544332',
         'Full Service, ABS Check, Accessories Fitting, Paint Touch-up', '9:30AM - 7PM', 4.4),
    ]

    # Create admin users (garage owners)
    for i, gdata in enumerate(garage_data):
        email = f'admin{i+1}@gobiker.com'
        pw = generate_password_hash('admin123')
        db.execute('INSERT INTO users (name, email, password, role, city, phone) VALUES (?,?,?,?,?,?)',
                   (f'Garage Owner {i+1}', email, pw, 'admin', gdata[2], gdata[4]))
        db.commit()
        uid = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()[0]
        db.execute('INSERT INTO garages (owner_id, name, address, city, phone, services, open_hours, rating) VALUES (?,?,?,?,?,?,?,?)',
                   (uid, gdata[0], gdata[1], gdata[2], gdata[3], gdata[4], gdata[5], gdata[6]))
        db.commit()

    # Create demo user
    pw = generate_password_hash('user123')
    db.execute('INSERT INTO users (name, email, password, role, city, phone) VALUES (?,?,?,?,?,?)',
               ('Arjun Kumar', 'user@gobiker.com', pw, 'user', 'Bengaluru', '9800011122'))
    db.commit()
    demo_uid = db.execute('SELECT id FROM users WHERE email=?', ('user@gobiker.com',)).fetchone()[0]

    # Add demo bikes
    bikes = [
        (demo_uid, 'Royal Enfield', 'Classic 350', 2021, 'KA01AB1234', 'Matt Black', 350, 7, 12500),
        (demo_uid, 'Honda', 'CB Shine', 2020, 'KA02CD5678', 'Red', 125, 9, 8200),
    ]
    for b in bikes:
        db.execute('INSERT INTO bikes (user_id, brand, model, year, reg_number, color, engine_cc, health_score, odometer, last_service_date) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (*b, (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')))
    db.commit()

    bike1 = db.execute('SELECT id FROM bikes WHERE reg_number=?', ('KA01AB1234',)).fetchone()[0]
    bike2 = db.execute('SELECT id FROM bikes WHERE reg_number=?', ('KA02CD5678',)).fetchone()[0]
    garage1 = db.execute('SELECT id FROM garages LIMIT 1').fetchone()[0]

    # Service records for bike1
    for i, (score, svc, note, cost, odo) in enumerate([
        (6, 'Engine Oil Change, Air Filter', 'Minor engine wear noticed', 850, 8000),
        (7, 'Chain Lubrication, Brake Pads', 'Good overall condition', 450, 10000),
        (7, 'Full Service, Spark Plug', 'Carburetor cleaned', 1200, 12500),
    ]):
        days_ago = (3 - i) * 45
        db.execute('INSERT INTO service_records (bike_id, garage_id, health_score, services_done, notes, cost, odometer, service_date) VALUES (?,?,?,?,?,?,?,?)',
                   (bike1, garage1, score, svc, note, cost, odo, (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')))

    # Fuel logs
    for i in range(5):
        db.execute('INSERT INTO fuel_logs (bike_id, liters, cost_per_liter, total_cost, odometer, log_date) VALUES (?,?,?,?,?,?)',
                   (bike1, round(random.uniform(3, 5), 1), 106.5,
                    round(random.uniform(3, 5) * 106.5, 2),
                    8000 + i * 800,
                    (datetime.now() - timedelta(days=i * 12)).strftime('%Y-%m-%d')))
    db.commit()
    print("✅ Demo data seeded. Login: user@gobiker.com / user123 | admin1@gobiker.com / admin123")
