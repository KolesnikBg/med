from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        doctor_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        FOREIGN KEY(patient_id) REFERENCES users(id),
                        FOREIGN KEY(doctor_id) REFERENCES users(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doctor_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        FOREIGN KEY(doctor_id) REFERENCES users(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS doctor_work_hours (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doctor_id INTEGER NOT NULL,
                        work_day TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        FOREIGN KEY(doctor_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Сохраняем пользователя в базе данных
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (first_name, last_name, email, password, role) VALUES (?, ?, ?, ?, ?)",
                       (first_name, last_name, email, password, role))
        conn.commit()
        conn.close()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Проверка данных пользователя
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

# Страница записи на прием (для администратора)
@app.route('/admin/appointment', methods=['GET', 'POST'])
def admin_appointment():
    if request.method == 'POST':
        patient_email = request.form['patient_email']
        doctor_email = request.form['doctor_email']
        date = request.form['date']
        time = request.form['time']

        # Найдем пациентов и врачей по email
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (patient_email,))
        patient = cursor.fetchone()

        cursor.execute("SELECT id FROM users WHERE email = ? AND role = 'doctor'", (doctor_email,))
        doctor = cursor.fetchone()

        if patient and doctor:
            cursor.execute("INSERT INTO appointments (patient_id, doctor_id, date, time) VALUES (?, ?, ?, ?)",
                           (patient[0], doctor[0], date, time))
            conn.commit()
            flash('Appointment created successfully!', 'success')
        else:
            flash('Invalid patient or doctor email.', 'danger')

        conn.close()
        return redirect(url_for('index'))

    return render_template('admin_appointment.html')

# Страница для администратора для выставления рабочих часов врача
@app.route('/admin/set_work_hours', methods=['GET', 'POST'])
def set_work_hours():
    if request.method == 'POST':
        doctor_email = request.form['doctor_email']
        work_day = request.form['work_day']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        # Найдем врача по email
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ? AND role = 'doctor'", (doctor_email,))
        doctor = cursor.fetchone()

        if doctor:
            cursor.execute("INSERT INTO doctor_work_hours (doctor_id, work_day, start_time, end_time) VALUES (?, ?, ?, ?)",
                           (doctor[0], work_day, start_time, end_time))
            conn.commit()
            flash('Work hours set successfully!', 'success')
        else:
            flash('Invalid doctor email.', 'danger')

        conn.close()
        return redirect(url_for('index'))

    return render_template('admin_set_work_hours.html')

# Запуск приложения
if __name__ == '__main__':
    init_db()  # Инициализируем базу данных, если еще не существует
    app.run(debug=True)
