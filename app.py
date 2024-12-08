from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Для сессий


# Создаем базы данных и таблицы
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('author', 'user'))
        )
    ''')

    # Таблица категорий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')

    # Таблица петиций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS petitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            required_signatures INTEGER NOT NULL,
            current_signatures INTEGER DEFAULT 0,
            status TEXT NOT NULL CHECK(status IN ('active', 'archived', 'deleted')),
            petition_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')

    # Таблица комментариев
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            petition_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            comment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (petition_id) REFERENCES petitions (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Таблица подписчиков (пользователей, подписавших петиции)
    cursor.execute('''
           CREATE TABLE IF NOT EXISTS subscribers (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               petition_id INTEGER NOT NULL,
               user_id INTEGER NOT NULL,
               FOREIGN KEY (petition_id) REFERENCES petitions (id),
               FOREIGN KEY (user_id) REFERENCES users (id)
           )
       ''')

    conn.commit()
    conn.close()


@app.route('/', methods=['GET'])
def index():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получение параметра категории из запроса
    category_id = request.args.get('category')

    # Если категория выбрана, фильтруем по ней, иначе показываем все активные петиции
    if category_id:
        cursor.execute('''
            SELECT p.id, p.name, p.description, c.name, p.required_signatures, p.current_signatures, p.status
            FROM petitions p
            JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active' AND p.category_id = ?
        ''', (category_id,))
    else:
        cursor.execute('''
            SELECT p.id, p.name, p.description, c.name, p.required_signatures, p.current_signatures, p.status
            FROM petitions p
            JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active'
        ''')

    petitions = cursor.fetchall()

    # Получение всех категорий
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()

    conn.close()

    # Проверка, авторизован ли пользователь
    is_logged_in = 'username' in session

    return render_template('index.html', petitions=petitions, categories=categories, is_logged_in=is_logged_in)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user_type = request.form['user_type']

        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, email, user_type) VALUES (?, ?, ?, ?)',
                           (username, password, email, user_type))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_type'] = user[4]
            return redirect('/')
        else:
            return render_template('login.html')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    return f"Welcome, {session['username']}! Your role: {session['user_type']}."


@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if 'username' not in session or session['user_type'] != 'author':
        return "Access denied. Only authors can create categories.", 403

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        conn.close()
        return redirect('/categories')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories')
    categories_list = cursor.fetchall()
    conn.close()
    # Проверка, авторизован ли пользователь
    is_logged_in = 'username' in session
    return render_template('categories.html', categories=categories_list, is_logged_in=is_logged_in)


@app.route('/petitions', methods=['GET', 'POST'])
def petitions():
    # Проверка прав доступа: только авторы могут создавать петиции
    if 'username' not in session or session['user_type'] != 'author':
        return "Access denied. Only authors can create petitions.", 403

    success_message = None

    if request.method == 'POST':
        # Получение данных из формы
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category']
        required_signatures = int(request.form['required_signatures'])

        # Подключение к базе данных
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Вставка новой петиции в таблицу
        cursor.execute(
            '''
            INSERT INTO petitions (author_id, name, description, category_id, required_signatures, status, current_signatures) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (session['user_id'], name, description, category_id, required_signatures, 'active', 0))
        conn.commit()

        # Сообщение об успехе
        success_message = f"Петиция '{name}' успешно создана!"
        conn.close()



    # Получение списка категорий для отображения в форме
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories')
    categories_list = cursor.fetchall()

    # Получение всех петиций с данными об авторах и категориях
    cursor.execute('''
        SELECT p.id, p.name, p.description, c.name AS category_name, 
               p.required_signatures, p.current_signatures, p.status, u.username AS author_name
        FROM petitions p
        JOIN categories c ON p.category_id = c.id
        JOIN users u ON p.author_id = u.id
        ORDER BY p.id DESC
    ''')
    petitions_list = cursor.fetchall()
    conn.close()
    # Проверка, авторизован ли пользователь
    is_logged_in = 'username' in session

    return render_template(
        'petitions.html',
        categories=categories_list,
        petitions=petitions_list,
        success_message=success_message,
        is_logged_in=is_logged_in
    )

# Переименуйте функцию или маршрут с уникальным именем
@app.route('/petition/<int:petition_id>', methods=['GET', 'POST'])
def petition_details_page(petition_id):  # Переименовываем функцию на уникальное имя
    if 'username' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получение информации о петиции
    cursor.execute('''
        SELECT p.id, p.name, p.description, c.name, p.required_signatures, p.current_signatures, p.status, u.username
        FROM petitions p
        JOIN categories c ON p.category_id = c.id
        JOIN users u ON p.author_id = u.id
        WHERE p.id = ?
    ''', (petition_id,))
    petition = cursor.fetchone()

    if not petition:
        conn.close()
        return "Petition not found.", 404

    # Проверка, подписан ли пользователь
    cursor.execute('SELECT * FROM subscribers WHERE petition_id = ? AND user_id = ?', (petition_id, user_id))
    subscription = cursor.fetchone()
    is_subscribed = True if subscription else False

    # Добавление комментария
    if request.method == 'POST':
        comment_text = request.form['comment_text']
        cursor.execute('INSERT INTO comments (petition_id, user_id, comment_text) VALUES (?, ?, ?)',
                       (petition_id, user_id, comment_text))
        conn.commit()

    # Получение комментариев
    cursor.execute('''
        SELECT c.comment_text, c.comment_date, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.petition_id = ?
        ORDER BY c.comment_date DESC
    ''', (petition_id,))
    comments = cursor.fetchall()
    conn.close()
    # Проверка, авторизован ли пользователь
    is_logged_in = 'username' in session

    return render_template('petition_details.html', petition=petition, comments=comments, is_subscribed=is_subscribed, is_logged_in=is_logged_in)

@app.route('/subscribe/<int:petition_id>', methods=['POST'])
def subscribe(petition_id):
    if 'username' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверим, подписан ли уже пользователь на эту петицию
    cursor.execute('SELECT * FROM subscribers WHERE petition_id = ? AND user_id = ?', (petition_id, user_id))
    existing_subscription = cursor.fetchone()

    if existing_subscription:
        conn.close()
        return "You are already subscribed to this petition.", 400

    # Добавим запись о подписке
    cursor.execute('INSERT INTO subscribers (petition_id, user_id) VALUES (?, ?)', (petition_id, user_id))
    conn.commit()

    # Обновим количество подписей в таблице petions
    cursor.execute('UPDATE petitions SET current_signatures = current_signatures + 1 WHERE id = ?', (petition_id,))
    conn.commit()
    conn.close()

    return redirect(f'/petition/{petition_id}')

@app.route('/petition/<int:petition_id>', methods=['GET', 'POST'])
def petition_details(petition_id):
    if 'username' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получение информации о петиции
    cursor.execute('''
        SELECT p.id, p.name, p.description, c.name, p.required_signatures, p.current_signatures, p.status, u.username
        FROM petitions p
        JOIN categories c ON p.category_id = c.id
        JOIN users u ON p.author_id = u.id
        WHERE p.id = ?
    ''', (petition_id,))
    petition = cursor.fetchone()

    if not petition:
        conn.close()
        return "Petition not found.", 404

    # Проверка, подписан ли пользователь
    cursor.execute('SELECT * FROM subscribers WHERE petition_id = ? AND user_id = ?', (petition_id, user_id))
    subscription = cursor.fetchone()
    is_subscribed = True if subscription else False

    # Добавление комментария
    if request.method == 'POST':
        comment_text = request.form['comment_text']
        cursor.execute('INSERT INTO comments (petition_id, user_id, comment_text) VALUES (?, ?, ?)',
                       (petition_id, user_id, comment_text))
        conn.commit()

    # Получение комментариев
    cursor.execute('''
        SELECT c.comment_text, c.comment_date, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.petition_id = ?
        ORDER BY c.comment_date DESC
    ''', (petition_id,))
    comments = cursor.fetchall()
    conn.close()

    return render_template('petition_details.html', petition=petition, comments=comments, is_subscribed=is_subscribed)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
