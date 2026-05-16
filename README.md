# GoBiker 🚴‍♂️

# Smart Bike Service & Garage Management Platform

GoBiker is a full-stack Flask web application designed for bike owners and garage admins to manage bike servicing, track vehicle health, maintain service history, log fuel usage, and discover trusted garages.

Built using **Flask + SQLite**, the platform provides separate dashboards for riders and garage owners with features like bike health scoring, service reminders, fuel tracking, and garage reviews.

---

# 🚀 Features

# 👤 User Features

* User Registration & Login
* Add and manage bikes
* View bike health score
* Track service history
* Fuel log management
* Service reminders
* Profile management
* Browse garages by city
* Review and rate garages

# 🛠 Garage Admin Features

* Separate admin dashboard
* Register a garage during signup
* Add bike service records
* Live bike lookup using registration number
* Update bike health score
* Manage garage details
* View customer service history

---

# 📸 Core Functionalities

| Module                    | Description                            |
| ------------------------- | -------------------------------------- |
| Bike Health Tracking      | Score bikes from 1–10                  |
| Service Records           | Store services, notes, cost & odometer |
| Fuel Logs                 | Maintain fuel expenses                 |
| Smart Reminders           | Alerts for overdue service             |
| Garage Finder             | Search garages city-wise               |
| Review System             | Ratings & comments                     |
| Role-Based Authentication | User & Admin access                    |

---

# 🧱 Tech Stack

# Backend

* Python
* Flask
* SQLite

# Frontend

* HTML
* CSS
* Jinja2 Templates

# Security

* Werkzeug Password Hashing

---

# 📂 Project Structure

```bash
go_biker/
│
├── app.py
├── database.py
├── gobiker.db
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── user_dashboard.html
│   ├── admin_dashboard.html
│   ├── bike_detail.html
│   ├── garages.html
│   ├── garage_detail.html
│   ├── add_bike.html
│   ├── edit_garage.html
│   ├── profile.html
│   └── new_service.html
```

---

# ⚙️ Installation

# 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/gobiker.git
cd gobiker
```

# 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate virtual environment:

# Windows

```bash
venv\Scripts\activate
```

# Linux / Mac

```bash
source venv/bin/activate
```

---

# 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies used: 

---

# 4️⃣ Run the Application

```bash
python app.py
```

Application runs on:

```bash
http://localhost:5000
```

---

# 🔐 Demo Login Credentials

# Rider Account

```text
Email: user@gobiker.com
Password: user123
```

# Garage Admin

```text
Email: admin1@gobiker.com
Password: admin123
```

Demo data and seeded garages are created automatically from the database setup. 

---

# 🗄 Database Schema

The project uses SQLite with the following tables:

* users
* garages
* bikes
* service_records
* fuel_logs
* reviews

Database initialization and schema creation are handled in `database.py`. 

---

# 🔑 Main Routes

# Public Routes

* `/`
* `/register`
* `/login`

# User Routes

* `/dashboard`
* `/bike/add`
* `/bike/<id>`
* `/garages`
* `/profile`

# Admin Routes

* `/admin/dashboard`
* `/admin/service/new`
* `/admin/garage/edit`

Defined inside Flask application routes. 

---

# 💡 Future Improvements

* Email notifications
* AI-based bike health prediction
* Google Maps garage integration
* Online service booking
* Payment gateway integration
* Mobile responsive UI
* REST API support

---

# 📚 Learning Outcomes

This project demonstrates:

* Flask routing
* Authentication & sessions
* SQLite database handling
* CRUD operations
* Role-based access control
* Full-stack web development
* Database relationships
* Service management systems

---

# 👨‍💻 Author

**Anik Chatterjee**
MCA Student | Full Stack & Frontend Developer

---

# 📜 License

This project is for educational and portfolio purposes.
