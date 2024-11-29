from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Petition, Signature, Comment, Category

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petition.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

# Главная страница
@app.route('/')
def index():
    petitions = Petition.query.filter_by(status='active').all()
    return render_template('index.html', petitions=petitions)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('index'))
        return "Invalid credentials"
    return render_template('login.html')

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Страница создания петиции
@app.route('/create_petition', methods=['GET', 'POST'])
def create_petition():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = request.form['category_id']
        required_signatures = int(request.form['required_signatures'])
        author_id = session.get('user_id')
        if author_id:
            new_petition = Petition(
                author_id=author_id,
                title=title,
                description=description,
                category_id=category_id,
                required_signatures=required_signatures
            )
            db.session.add(new_petition)
            db.session.commit()
            return redirect(url_for('index'))
        return "Unauthorized"
    categories = Category.query.all()
    return render_template('create_petition.html', categories=categories)

# Страница петиции
@app.route('/petition/<int:petition_id>', methods=['GET', 'POST'])
def petition(petition_id):
    petition = Petition.query.get(petition_id)
    comments = Comment.query.filter_by(petition_id=petition_id).all()
    if request.method == 'POST':
        user_id = session.get('user_id')
        if user_id and request.form.get('comment'):
            content = request.form['comment']
            new_comment = Comment(petition_id=petition_id, user_id=user_id, content=content)
            db.session.add(new_comment)
            db.session.commit()
        elif user_id:
            new_signature = Signature(petition_id=petition_id, user_id=user_id)
            db.session.add(new_signature)
            petition.current_signatures += 1
            if petition.current_signatures >= petition.required_signatures:
                petition.status = 'archived'
            db.session.commit()
        return redirect(url_for('petition', petition_id=petition_id))
    return render_template('petition.html', petition=petition, comments=comments)

# Архив
@app.route('/archive')
def archive():
    petitions = Petition.query.filter_by(status='archived').all()
    return render_template('archive.html', petitions=petitions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создание таблиц, если их еще нет
    app.run(debug=True)
