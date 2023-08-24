from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
import os
import sqlite3 as sq
from FDataBase import FDataBase # Мой класс, для работы с БД
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin # Мой класс, для работы с Фласк-Логин
import re

# Настройки
DATABASE = '/tmp/saper.db'
DEBUG = True
SECRET_KEY = 'pjih34obsbufv8657gysuncklsdmc8nmwe67'
MAX_CONTENT_LENGTH = 1024*1024

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'saper.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Пожалуйста, авторизуйтесь для доступа к странице"
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, dbase)


def connect_db():  # создаем подключение к базе данных
    conn = sq.connect(app.config['DATABASE'])
    conn.row_factory = sq.Row
    return conn


def get_db():  # соединение с БД если оно не установлено
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.teardown_appcontext
def close_db(error):  # разрываем соединение с БД (если оно было установлено)
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.errorhandler(404) # Обработчик ошибки "404"
def pageNotFound(error):
    return render_template('404error.html', title="Страница не найдена", menu=dbase.getMenu())

dbase = None

@app.before_request # Соединение с БД перед началом каждой функции
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.route('/reg', methods=['POST', 'GET'])  # Регистрация
def reg():
    if request.method == 'POST':
        if len(request.form['login']) > 2 and len(request.form['pass']) > 5 and bool(re.search('^[a-zA-Z0-9_]*$',request.form['login']))==True:
            hash = generate_password_hash(request.form['pass'])
            res = dbase.addUser(request.form['username'], request.form['login'], request.form['mail'], hash)
            if res:
                flash("Регистрация прошла успешно", "success")
                return redirect(url_for('login'))
            else:
                # return redirect(url_for('reg'))
                flash("Ошибка при добавлении в БД", "error")
        else:
            # return redirect(url_for('/reg'))
            flash("Ошибка регистрации: пароль/логин слишком короткие и/или использование запрещенных спец.символов в логине", "error")

    return render_template('reg.html', title="Регистрация", menu=dbase.getMenu())


@app.route("/login", methods=['POST', 'GET'])  # Авторизация
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        user = dbase.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['password'], request.form['pass']):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get('remain') else False
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for('profile'))

        flash("Неверный логин и/или пароль", "error")

    return render_template('login.html', title="Авторизация", menu=dbase.getMenu())


@app.route("/logout") # Выход из профиля
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("login"))

@app.route("/profile") # Профиль пользователя
@login_required
def profile():
    return render_template('profile.html', title="Профиль: " + current_user.getName(), menu=dbase.getMenu(), posts=dbase.getMyPet(current_user.getName()))

@app.route("/userava") # Отображение аватарки пользователя в профиле
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/jpg'
    return h

@app.route("/upload", methods=["POST", "GET"]) # Смена аватарки пользователя
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка загрузки аватара", "error")
                flash("Аватар загружен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))


@app.route("/")  # Главная страница
def index():
    return render_template('index.html', title="My pets", menu=dbase.getMenu())
@app.route("/contacts", methods=["POST", "GET"])  # Контакты
def contacts():
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')

    return render_template('contacts.html', title="Контакты", menu=dbase.getMenu())


@app.route("/all_pets", methods=["POST", "GET"])  # Все животные
def all_pets():
    return render_template('all_pets.html', title="Все животные", menu=dbase.getMenu(), posts=dbase.getPetsAnonce())


@app.route("/add_pet", methods=["POST", "GET"]) # Добавить питомца
@login_required
def add_pet():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
            except:
                flash("Ошибка загрузки фотографии", "error")
        else:
            with app.open_resource(app.root_path + url_for('static', filename='pet_image/pix_art.jpg'), "rb") as f:
                img = f.read()
        res = dbase.add_pets(request.form['petname'], current_user.getName(), request.form['old'], "Да" if request.form.get('ifHome') else "Нет",img)
        if not res:
            flash("Ошибка добавления питомца", "error")
        else:
            flash("Питомец добавлен успешно", "success")
    return render_template('add_pet.html', menu=dbase.getMenu(), title='Добавить питомца')


@app.route("/edit_pet/<int:id_pet>", methods=["POST","GET"]) # Изменение профиля питомца (только хозяин)
@login_required
def edit_pet(id_pet):
    name, owner, old, home, foto_1 = dbase.getPet(id_pet)
    if current_user.getName() != owner:
        abort(404)

    if request.method == 'POST':

        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
            except:
                flash("Ошибка загрузки фотографии", "error")
        else:
            img = dbase.getPet(id_pet)['foto_1']

        res = dbase.editPets(id_pet,request.form['petname'], request.form['old'], "Да" if request.form.get('ifHome') else "Нет", img)
        if not res:
            flash("Ошибка сохранения профиля", "error")
        else:
            flash("Профиль питомца успешно сохранен", "success")
            name, owner, old, home, foto_1 = dbase.getPet(id_pet)

    if home == 'Да':
        check = 'checked'
    else:
        check = 'unchecked'
    return render_template('edit_pet.html', menu=dbase.getMenu(), title='Редактирование профиля: ' + name, post = {'petAva':'/getPetAva/' + str(id_pet),'del_id':'/del_pet/' + str(id_pet),'id':'/edit_pet/' + str(id_pet),'name':name,'owner':owner,'old':old,'home':check})



@app.route("/del_pet/<int:id_pet>", methods=["POST","GET"]) # Удаление питомца
@login_required
def del_pet(id_pet):
    name, owner, old, home, foto_1 = dbase.getPet(id_pet)
    if current_user.getName() != owner:
        abort(404)
    if request.method == 'POST':
        res = dbase.delPets(id_pet)
        if not res:
            flash("Ошибка удаления профиля питомца", "error")
            return redirect("/edit_pet/" + str(id_pet))
        else:
            flash("Профиль питомца успешно удален", "success")
    return redirect(url_for('profile'))

