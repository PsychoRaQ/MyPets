from flask_login import UserMixin
from flask import url_for

class UserLogin(UserMixin):

    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self
    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['user_id'])

    def getUsername(self):
        return self.__user['username'] if self.__user else "Без имени"

    def getEmail(self):
        return self.__user['email'] if self.__user else "Без email"

    def getName(self):
        return self.__user['name'] if self.__user else "Без имени"

    def getAdminRoot(self):
        return True if self.__user['admin'] == 1 else False

    def getAvatar(self, app):
        img = False
        if not self.__user['avatar']:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default.jpg'),"rb") as f:
                    img = f.read()
            except  FileNotFoundError as e:
                print(str(e))
        else:

            img = self.__user['avatar']

        return img

    def verifyExt(self, filename):
        ext = filename.rsplit('.', 1)[1]
        if ext == "jpg" or ext == "JPG":
            return True
        return False