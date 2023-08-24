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
                return False

            return res
        except sqlite3.Error as e:
            print(str(e))

        return False

    def updateUserProfile(self, username,email, avatar, user_id): # Обновить аватарку пользователя
        if not avatar:
            return False

        try:
            binary = sqlite3.Binary(avatar)
            self.__cur.execute(f"UPDATE my_pet_users SET username = ?,email = ?, avatar = ? WHERE user_id = ? ", (username,email,binary,user_id))
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
            sql = 'SELECT * FROM mainmenu WHERE id < 5'
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print('Ошибка')
            return []

    def getPet(self, pet_id): # Получение данных питомца по id
        try:
            self.__cur.execute(f"SELECT name,owner, owner_id, old, home, foto_1,about FROM allpets WHERE id = ? LIMIT 1", (pet_id,))
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
                return res
        except sqlite3.Error as e:
            print(str(e))
        return []

    def getPetsAnonce(self): # получение списка всех питомцев в базе (для "все питомцы")
        try:
            self.__cur.execute(f"SELECT id,name,owner,owner_id,old,home FROM allpets ORDER BY id DESC")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(str(e))
        return []

    def add_pets(self, petname, owner, old, home, img, about): # Добавление питомца в БД
        pet_ava = sqlite3.Binary(img)
        try:
            self.__cur.execute("INSERT INTO allpets VALUES(NULL,?,?,?,?,?,?,?)", (petname, old, owner,current_user.get_id(), home, pet_ava,about))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def editPets(self, pet_id, petname, old, home, img,about): # Редактирование данных питомца в БД // сделал в виде функции?
        pet_ava = sqlite3.Binary(img)
        try:
            self.__cur.execute("UPDATE allpets SET name = ?, old = ?, home = ?, foto_1 = ?, about = ? WHERE id = ?",(petname, old, home, pet_ava, about, pet_id))
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

    def getAllUsers(self): # получение списка всех пользователей сайта (для админа)
        try:
            self.__cur.execute(f"SELECT user_id,username,name,email FROM my_pet_users ORDER BY user_id DESC")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(str(e))
        return []

    def addUserRequest(self,user_id,username,email,msg,date): # создать новое обращение от формы обратной связи
        try:
            self.__cur.execute("INSERT INTO contacts VALUES(NULL,?,?,?,?,?,'')", (username, email, user_id, msg, date,))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def getRequest(self): # получить данные всех обращений пользователей
        try:
            self.__cur.execute(f"SELECT * FROM contacts ORDER BY date DESC")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(str(e))
        return []

    def getRequest_by_id(self,req_id): # получить обращение по его ID
        try:
            self.__cur.execute(f"SELECT * FROM contacts WHERE id = ?", (req_id,))
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(str(e))
        return False

    def updateUserRequest(self, res_id, resume): # отправка ответа администратора на обращение
        try:
            self.__cur.execute("UPDATE contacts SET resume = ? WHERE id = ?",(resume, res_id))
            self.__db.commit()
        except sqlite3.Error as e:
            print(str(e))
            return False
        return True

    def getMyRequest(self): # получить обращение по его ID
        try:
            self.__cur.execute(f"SELECT * FROM contacts WHERE user_id = ? ORDER BY id DESC", (current_user.get_id(),))
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(str(e))
        return False