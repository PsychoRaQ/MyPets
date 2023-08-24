from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
import os
import sqlite3 as sq
from FDataBase import FDataBase  # Мой класс, для работы с БД
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin  # Мой класс, для работы с Фласк-Логин
import re
import datetime

# Настройки
DATABASE = '/tmp/saper.db'
DEBUG = True
SECRET_KEY = 'pjih34obsbufv8657gysuncklsdmc8nmwe67'
MAX_CONTENT_LENGTH = 1024 * 1024

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


@app.errorhandler(404)  # Обработчик ошибки "404"
def pageNotFound(error):
    return render_template('404error.html', title="Страница не найдена", menu=dbase.getMenu())


dbase = None


@app.before_request  # Соединение с БД перед началом каждой функции
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.route('/reg', methods=['POST', 'GET'])  # Регистрация
def reg():
    if request.method == 'POST':
        if len(request.form['login']) > 2 and len(request.form['pass']) > 5 and bool(
                re.search('^[a-zA-Z0-9_]*$', request.form['login'])) == True:
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
            flash(
                "Ошибка регистрации: пароль/логин слишком короткие и/или использование запрещенных спец.символов в логине",
                "error")

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
            return redirect(request.args.get("next") or url_for('profile', user_id=current_user.get_id()))

        flash("Неверный логин и/или пароль", "error")

    return render_template('login.html', title="Авторизация", menu=dbase.getMenu())


@app.route("/logout")  # Выход из профиля
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def redir_profile():
    return redirect("profile/" + str(current_user.get_id()))


@app.route("/profile/<int:user_id>")  # Профиль пользователя
@login_required
def profile(user_id):
    if not user_id or user_id == int(current_user.get_id()):
        user_id = current_user.get_id()
        return render_template('profile.html', title="Профиль: " + current_user.getName(), menu=dbase.getMenu(),
                               posts=dbase.getMyPet(current_user.getName()))
    if not dbase.getUser(user_id):
        abort(404)
    if user_id != current_user.get_id():
        profile_info = dbase.getUser(user_id)
        return render_template('profile_not_my.html', title="Профиль: " + dbase.getUser(user_id)['name'],
                               menu=dbase.getMenu(), posts=dbase.getMyPet(dbase.getUser(user_id)['name']),
                               profile_info=dbase.getUser(user_id))


@app.route("/userava")  # Отображение аватарки пользователя в профиле
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/jpg'
    return h

@app.route("/profile_edit", methods=["POST", "GET"])
@login_required
def profile_edit():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            img = current_user.getAvatar(app)
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
            except FileNotFoundError as e:
                print(str(e))
        res = dbase.updateUserProfile(request.form['username'],request.form['email'], img, current_user.get_id())
        if not res:
                flash("Ошибка обновления профиля", "error")
        flash("Профиль успешно сохранен", "success")
    return render_template('profile_edit.html', menu=dbase.getMenu(), title='Редактирование профиля: ' + current_user.getName(),
                           post={'username': current_user.getUsername(), 'email': current_user.getEmail()})




@app.route("/upload", methods=["POST", "GET"])  # Смена аватарки пользователя
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

    return redirect(url_for('profile', user_id = current_user.get_id()))


@app.route("/")  # Главная страница
def index():
    return render_template('index.html', title="My pets", menu=dbase.getMenu())


@app.route("/contacts", methods=["POST", "GET"])  # Контакты
@login_required
def contacts():
    if request.method == 'POST':
        if len(request.form['username']) > 2:

            res = dbase.addUserRequest(current_user.get_id(),request.form['username'], request.form['email'], request.form.get('msg'),datetime.datetime.now().strftime("%Y-%m-%d, %H:%M"))
            if not res:
                flash('Ошибка отправки. Попробуйте снова.', category='error')
            else:
                flash('Сообщение отправлено. Отследить статус заявки Вы можете в своем профиле.', category='success')
                return redirect(url_for('contacts'))
        else:
            flash('Ошибка отправки: Имя слишком короткое', category='error')

    return render_template('contacts.html', title="Обратная связь", menu=dbase.getMenu())


@app.route("/all_pets", methods=["POST", "GET"])  # Все животные
def all_pets():
    return render_template('all_pets.html', title="Все животные", menu=dbase.getMenu(), posts=dbase.getPetsAnonce())


@app.route("/add_pet", methods=["POST", "GET"])  # Добавить питомца
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
        res = dbase.add_pets(request.form['petname'], current_user.getName(), request.form['old'],
                             "Да" if request.form.get('ifHome') else "Нет", img, request.form.get('about'))
        if not res:
            flash("Ошибка добавления питомца", "error")
        else:
            flash("Питомец добавлен успешно", "success")
    return render_template('add_pet.html', menu=dbase.getMenu(), title='Добавить питомца')


@app.route("/edit_pet/<int:id_pet>", methods=["POST", "GET"])  # Изменение профиля питомца (только хозяин)
@login_required
def edit_pet(id_pet):
    getPet = dbase.getPet(id_pet)
    if not current_user.getAdminRoot():
        if current_user.getName() != getPet['owner']:
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

        res = dbase.editPets(id_pet, request.form['petname'], request.form['old'],
                             "Да" if request.form.get('ifHome') else "Нет", img, request.form.get('about'))
        if not res:
            flash("Ошибка сохранения профиля", "error")
        else:
            flash("Профиль питомца успешно сохранен", "success")
            getPet = dbase.getPet(id_pet)

    if getPet['home'] == 'Да':
        check = 'checked'
    else:
        check = 'unchecked'
    return render_template('edit_pet.html', menu=dbase.getMenu(), title='Редактирование профиля: ' + getPet['name'],
                           post={'id': id_pet, 'name': getPet['name'], 'owner': getPet['owner'], 'old': getPet['old'], 'home': check, 'about': getPet['about']})


@app.route("/del_pet/<int:id_pet>", methods=["POST", "GET"])  # Удаление питомца
@login_required
def del_pet(id_pet):
    name, owner, old, home, foto_1, about = dbase.getPet(id_pet)
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


@app.route("/pet/<int:id_pet>")  # Обработчик профиля питомца
def showPet(id_pet):
    getPet = dbase.getPet(id_pet)
    if not getPet['name']:
        abort(404)
    return render_template('pet_profile.html', menu=dbase.getMenu(), title=getPet['name'],
                           post={'id': id_pet, 'name': getPet['name'], 'owner': getPet['owner'],
                                 'owner_id': getPet['owner_id'], 'old': getPet['old'], 'home': getPet['home'],
                                 'about': getPet['about']})


@app.route("/getPetAva/<int:id_pet>")  # Получение аватарки питомца
def getPetAva(id_pet):
    img = dbase.getPet(id_pet)['foto_1']
    return img

@app.route("/getUserava/<int:user_id>")
@login_required
def getUserava(user_id):
    if not current_user.getAdminRoot():
        abort(404)
    img = dbase.getUser(user_id)['avatar']
    if not img:
        try:
            with app.open_resource(app.root_path + url_for('static', filename='images/default.jpg'),"rb") as f:
                img = f.read()
        except:
            print('Ошибка загрузки аватарки пользователя: ' + str(user_id))
    return img

@app.route("/admin")  # Получение данных о наличии админки
@login_required
def admin():
    if not current_user.getAdminRoot():
        abort(404)
    return render_template('admin.html', menu=dbase.getMenu(), title='Администрирование')

@app.route("/admin_editProfile") # админка - редактрование профиля пользователя
@login_required
def admin_editProfile():
    if not current_user.getAdminRoot():
        abort(404)
    return render_template('admin_edit_profile.html', menu=dbase.getMenu(), title='Администрирование', posts = dbase.getAllUsers())

@app.route("/admin_edit_profile_with_id/<int:user_id>", methods=['POST','GET']) # админка - редактрование профиля пользователя(метод)
@login_required
def admin_edit_profile_with_id(user_id):
    if not current_user.getAdminRoot():
        abort(404)
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            try:
                img = dbase.getUser(user_id)['avatar']
            except:
                img = dbase.getUser(user_id)['avatar']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
            except FileNotFoundError as e:
                print(str(e))
        res = dbase.updateUserProfile(request.form['username'], request.form['email'], img, user_id)
        if not res:
            flash("Ошибка обновления профиля", "error")
        flash("Профиль успешно сохранен", "success")
    return render_template('admin_edit_profile.html', menu=dbase.getMenu(), title='Администрирование', posts = dbase.getAllUsers())

@app.route('/admin_editPet') # админка - редактрование профиля животного
@login_required
def admin_editPet():
    if not current_user.getAdminRoot():
        abort(404)
    return render_template('admin_edit_pet.html', title="Администрирование", menu=dbase.getMenu(), posts=dbase.getPetsAnonce())

@app.route('/admin_resume') # админка - обращения пользователя
@login_required
def admin_resume():
    if not current_user.getAdminRoot():
        abort(404)
    return render_template('resume_contacts.html', title="Администрирование", menu=dbase.getMenu(),  posts=dbase.getRequest())

@app.route('/resume_id/<int:res_id>', methods=['POST','GET']) # админка - ответ на обращение пользователя
@login_required
def resume_id(res_id):
    if not current_user.getAdminRoot():
        abort(404)
    if request.method == 'POST':
        res = dbase.updateUserRequest(res_id,request.form.get('resume'))
        if not res:
            flash("Ошибка: не удалось отравить ответ", "error")
        else:
            flash("Ответ успешно отправлен", "success")
        return redirect(url_for('resume_id',res_id = res_id))

    return render_template('admin_resume.html', title="Ответ на заявку №" + str(res_id), menu=dbase.getMenu(), posts=dbase.getRequest_by_id(res_id))

@app.route('/my_request') # просмотр своих отправленных обращений
@login_required
def my_request():
    resume = dbase.getMyRequest()
    if resume == False:
        flash("У вас нет ни одного обращения", "error")
        return redirect(url_for('profile', user_id = current_user.get_id()))
    return render_template('my_request.html', title="Ваши обращения: ", menu=dbase.getMenu(), posts=resume)


if __name__ == "__main__":
    app.run(debug=True)
