from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from sys import stderr
import sys
from package.mainwindow import (
    MainWindow,
    Login,
)
from package.model import Model


class Controller(QObject):
    model_changed = pyqtSignal()
    DRUG=1
    PROP=2
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.model = Model()
        self.login = Login(self)
        self.login.show()
        self.login.accepted.connect(self.login_attempt)
        self.app.exec_()

    def login_attempt(self):
        while True:
            username = self.login.get_username()
            password = self.login.get_password()
            if username == password and (username == 'user' or username == 'admin'):
                self.admin = username == 'admin'
                self.window = MainWindow(self)
                self.window.show()
                break
            self.login = Login(self)
            self.login.exec_()
            continue

    def qsql_table_model(self, tablename, types):
        return self.model.qsql_table_model(tablename, types)

    def analysis(self, things):
        return self.model.analysis(things)

    def add_thing(self, name, dsc, types):
        ret = self.model.add_thing(name, dsc, types)
        if ret is not None:
            self.model_changed.emit()
        return ret

    def add_rule(self, name, dsc, things):
        ret = self.model.add_rule(name, dsc, things)
        self.model_changed.emit()
        return ret

    def thing_by_name(self, name):
        return self.model.thing_by_name(name)

    def remove_rule(self, rule):
        ret = self.model.remove_rule(rule)
        self.model_changed.emit()
        return ret

    def remove_thing(self, thing):
        ret = self.model.remove_thing(thing)
        self.model_changed.emit()
        return ret

    def things(self, types):
        return self.model.things(types)

    def rules(self):
        return self.model.rules()

    def update_dsc(self, thing, dsc):
        self.model.update_dsc(thing, dsc)
        self.model_changed.emit()
