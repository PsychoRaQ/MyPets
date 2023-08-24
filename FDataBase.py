import sqlite3
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def addUser(self, username, name, mail, password): # Добавить пользователя в БД (регистрация)
        try:
            self.__cur.execute(f"SELECT COUNT() as `count` FROM my_pet_users WHERE email = ? OR name = ?", (mail,name))
            res = self.__cur.fetchone()
            if res['count'] > 0:
                return False
            self.__cur.execute("INSERT INTO my_pet_users VALUES(NULL,?,?,?,?,NULL,0)", (username, name, mail, password))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def getUser(self, user_id): # получение данных пользователя (для Фласк-логин)по id
        try:
            self.__cur.execute(f"SELECT * FROM my_pet_users WHERE user_id = ? LIMIT 1", (user_id,))
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            return res

        except sqlite3.Error as e:
            print(str(e))

        return False


    def getUserByEmail(self, email): # Получить данные пользователя по E-Mail (для авторизации)
        try:
            self.__cur.execute(f"SELECT * FROM my_pet_users WHERE email = ? LIMIT 1", (email,))
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False

            return res
        except sqlite3.Error as e:
            print(str(e))

        return False

    def updateUserAvatar(self, avatar, user_id): # Обновить аватарку пользователя
        if not avatar:
            return False

        try:
            binary = sqlite3.Binary(avatar)
            self.__cur.execute(f"UPDATE my_pet_users SET avatar = ? WHERE user_id = ? ", (binary,user_id))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def getMenu(self): # Отображение меню у клиента (получение из БД)
        if current_user.is_authenticated:
            sql = 'SELECT * FROM mainmenu WHERE id != 4 and id != 7'
            if current_user.getAdminRoot() == 1:
                sql = 'SELECT * FROM mainmenu WHERE id != 4'
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print('Ошибка')
            return []
        else:
            sql = '''SELECT * FROM mainmenu WHERE id < 5'''
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print('Ошибка')
            return []



    def getPet(self, pet_id): # Получение данных питомца по id
        try:
            self.__cur.execute(f"SELECT name,owner,old, home, foto_1 FROM allpets WHERE id = ? LIMIT 1", (pet_id,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            print(str(e))
        return (False, False)


    def getMyPet(self, owner): # Получение списка питомцев (для пользователя в профиль)
        try:
            self.__cur.execute(f"SELECT id,name,old,home FROM allpets WHERE owner = ? ORDER BY id DESC", (owner,))
            res = self.__cur.fetchall()
            if res:
                print(res)
                return res
        except sqlite3.Error as e:
            print(str(e))
        return []

    def getPetsAnonce(self): # получение списка всех питомцев в базе (для "все питомцы")
        try:
            self.__cur.execute(f"SELECT id,name,owner,old,home FROM allpets ORDER BY id DESC")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(str(e))
        return []

    def add_pets(self, petname, owner, old, home, img): # Добавление питомца в БД
        pet_ava = sqlite3.Binary(img)
        try:
            self.__cur.execute("INSERT INTO allpets VALUES(NULL,?,?,?,?,?,NULL,NULL)", (petname, old, owner, home, pet_ava))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def editPets(self, pet_id, petname, old, home, img): # Редактирование данных питомца в БД // сделал в виде функции?
        pet_ava = sqlite3.Binary(img)
        try:
            a = """UPDATE allpets SET name = ?, old = ?, home = ?, foto_1 = ? WHERE id = ?"""
            b = (petname, old, home, pet_ava, pet_id)
            self.__cur.execute(a, b)
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def delPets(self,pet_id): # Удаление питомца из БД
        try:
            self.__cur.execute("DELETE FROM allpets WHERE id = ?", (pet_id,))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True
