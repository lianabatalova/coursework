from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from package.build import (
    mainwindow,
)
from package.model import (
    Rule,
    Thing,
)
from package.helpers import *
from sys import stderr
from copy import deepcopy


class MainWindow(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self, controller):
        super().__init__()
        self.setupUi(self)

        self.controller = controller
        self.controller.model_changed.connect(self.model_changed)
        self.widget.setLayout(QVBoxLayout())
        self.thingsWidget = None
        self.model_changed()
        self.menuManage.setEnabled(self.controller.admin)

        self.setAttribute(Qt.WA_DeleteOnClose, True);

        self.analysis_pb.clicked.connect(self.analysis_clicked)

    def model_changed(self):
        if self.thingsWidget is not None:
            self.thingsWidget.hide()
            self.widget.layout().removeWidget(self.thingsWidget)
        self.thingsWidget = ThingsWidget(self.controller, readOnly=False)
        self.widget.layout().addWidget(self.thingsWidget)

    def analysis_clicked(self):
        things = self.thingsWidget.things()
        rules = self.controller.analysis(things)
        result_window = ResultDialog(self.controller, rules)
        result_window.exec_()

    def info_message(self):
        info_w = InfoMessage()
        info_w.exec_()

    def logout(self):
        self.close()

    def manage_preparations(self):
        manage_w = ManageThings(self.controller, self.controller.DRUG, 'Редактировать препараты')
        manage_w.exec_()

    def manage_properties(self):
        manage_w = ManageThings(self.controller, self.controller.PROP, 'Редактировать свойства')
        manage_w.exec_()

    def manage_rules(self):
        manage_w = ManageRules(self.controller)
        manage_w.exec_()
