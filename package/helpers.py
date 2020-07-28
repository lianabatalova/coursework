from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from package.build import (
    mainwindow,
    login,
    things_widget,
    thing,
    result,
    rule,
    info,
    manage,
)
from package.model import (
    Rule,
    Thing,
)
from sys import stderr
from copy import deepcopy


class Login(QDialog, login.Ui_Dialog):
    def __init__(self, controller):
        super().__init__()
        self.setupUi(self)
        self.controller = controller
        self.buttonBox.accepted.connect(self.some_lambda)
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Ok).setText('Войти')
        self.buttonBox.button(QDialogButtonBox.Close).setText('Закрыть')

    def get_username(self):
        return self.username.text()

    def get_password(self):
        return self.password.text()

    def some_lambda(self):
        self.close()
        self.accepted.emit()


class InfoMessage(QDialog, info.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Ok).setText('Закрыть')
        self.textBrowser.setAttribute(Qt.WA_TranslucentBackground)


class ListRuleItem(QListWidgetItem):
    def __init__(self, rule, parent=None):
        super().__init__(rule.name, parent)
        self.rule = rule


class ListThingItem(QListWidgetItem):
    def __init__(self, thing, parent=None):
        super().__init__(thing.name, parent)
        self.thing = thing


class RuleDialog(QDialog, rule.Ui_Dialog):
    def __init__(self, controller, rule=None, readOnly=True):
        super().__init__()
        self.setupUi(self)

        self.controller = controller
        self.widget.setLayout(QVBoxLayout())
        self.thingsWidget = ThingsWidget(self.controller, readOnly=readOnly)
        self.widget.layout().addWidget(self.thingsWidget)

        self.name_lineEdit.setReadOnly(readOnly)
        self.dsc.setReadOnly(readOnly)

        if readOnly:
            self.buttonBox.clear()
            self.buttonBox.addButton(QDialogButtonBox.Ok)
            self.buttonBox.button(QDialogButtonBox.Ok).setText('Закрыть')
        else:
            self.buttonBox.button(QDialogButtonBox.Cancel).setText('Отмена')
            self.buttonBox.button(QDialogButtonBox.Save).setText('Сохранить')

        self.rule = rule
        if rule is not None:
            self.name_lineEdit.setText(rule.name)
            self.dsc.setPlainText(rule.dsc)
            for thing in rule.things:
                self.thingsWidget.add_thing(thing)

    def get_name(self):
        return self.name_lineEdit.text()

    def get_dsc(self):
        return self.dsc.toPlainText()

    def get_things(self):
        return self.thingsWidget.things()

    def setup_by(self, rule):
        if rule is None:
            return
        self.name_lineEdit.setText(rule.name)
        for thing in rule.things:
            self.graphics_scene.append(thing)
        self.dsc.setPlainText(rule.dsc)


class ResultDialog(QDialog, result.Ui_Dialog):
    def __init__(self, controller, rules):
        super().__init__()
        self.setupUi(self)
        self.controller = controller
        for rule in rules:
            self.result_lw.addItem(ListRuleItem(rule))
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Ok).setText('Закрыть')
        self.result_lw.itemDoubleClicked.connect(self.rule_clicked)

    def rule_clicked(self, item):
        rule = item.rule
        self.rule_window = RuleDialog(self.controller, rule)
        ret = self.rule_window.exec_()


class ThingDialog(QDialog, thing.Ui_Dialog):
    def __init__(self, controller, thing=None, readOnly=True, fixed_name=False):
        super().__init__()
        self.setupUi(self)
        self.controller = controller
        if thing:
            self.dsc.setPlainText(thing.dsc)
            self.name_lineEdit.setText(thing.name)
        self.dsc.setReadOnly(readOnly)
        self.name_lineEdit.setReadOnly(readOnly)
        if readOnly:
            self.buttonBox.clear()
            self.buttonBox.addButton(QDialogButtonBox.Ok)
            self.buttonBox.button(QDialogButtonBox.Ok).setText('Закрыть')
            self.buttonBox.accepted.connect(self.close)
        if fixed_name:
            self.name_lineEdit.setReadOnly(True)
            self.buttonBox.button(QDialogButtonBox.Save).setText('Сохранить')
            self.buttonBox.button(QDialogButtonBox.Cancel).setText('Отмена')

    def get_name(self):
        return self.name_lineEdit.text()

    def get_dsc(self):
        return self.dsc.toPlainText()


class ThingsWidget(QWidget, things_widget.Ui_Form):
    def __init__(self, controller, readOnly=True):
        super().__init__()
        self.setupUi(self)
        self.controller = controller
        if readOnly:
            self.remove_pb.hide()
            self.thing_lineEdit.setReadOnly(True)
            self.thing_lineEdit.setPlaceholderText('Для внесения изменений войдите под пользователем admin.')
        else:
            self.remove_pb.clicked.connect(self.remove_clicked)
            self.setup_completer()
        self.setup_toolButton(readOnly)
        self.setup_checkboxes(readOnly)
        self.selected_lw.itemDoubleClicked.connect(self.thing_clicked)

    def setup_completer(self):
        self.completer = QCompleter(self.thing_lineEdit)
        self.completer.setModel(self.controller.qsql_table_model('things',
                                                                 [self.controller.DRUG]))
        self.completer.setCompletionColumn(1)
        self.completer.activated.connect(self.completer_activated)
        self.thing_lineEdit.setCompleter(self.completer)

    def setup_toolButton(self, readOnly):
        self.menu = QMenu(self)
        props = self.controller.things(types=self.controller.PROP)
        for prop in props:
            action = QAction(prop.name, self)
            action.setCheckable(True)
            action.toggled.connect(self.action_toggled)
            action.setDisabled(readOnly)
            self.menu.addAction(action)
        # self.toolButton.setMenu(self.menu)

    def setup_checkboxes(self, readOnly):
        self.frameLayout.setAlignment(Qt.AlignTop)
        props = self.controller.things(types=self.controller.PROP)
        for prop in props:
            checkBox = QCheckBox(prop.name, self)
            self.frameLayout.addWidget(checkBox)

    def action_toggled(self, _):
        self.menu.show()
        name = self.sender().text()
        thing = self.controller.thing_by_name(name)
        self.toggle_select(thing)

    def toggle_select(self, thing):
        item = self.item_in_selected(thing)
        if not item:
            item = ListThingItem(thing)
            self.selected_lw.addItem(item)
        else:
            for i in range(self.selected_lw.count()):
                item = self.selected_lw.item(i)
                if item.thing == thing:
                    self.selected_lw.takeItem(i)
                    break

    def remove_clicked(self):
        items = [index.row() for index in self.selected_lw.selectedIndexes()]
        items.sort(reverse=True)
        for idx in items:
            item = self.selected_lw.item(idx)
            deleted = False
            for action in self.menu.actions():
                if item.thing.name == action.text():
                    action.setChecked(False)
                    deleted = True
                    break
            if not deleted:
                self.selected_lw.takeItem(idx)

    def item_in_selected(self, thing):
        for i in range(self.selected_lw.count()):
            item = self.selected_lw.item(i)
            if item.thing == thing:
                return item
        return None

    def completer_activated(self, text):
        thing = self.controller.thing_by_name(text)
        if thing is None:
            return
        if not self.item_in_selected(thing):
            self.toggle_select(thing)

    def things(self):
        things = []
        for i in range(self.selected_lw.count()):
            thing = self.selected_lw.item(i).thing
            things.append(thing)
        return things

    def thing_clicked(self, item):
        thing = item.thing
        self.thing_window = ThingDialog(self.controller, thing)
        ret = self.thing_window.exec_()

    def add_thing(self, thing):
        item = self.item_in_selected(thing)
        if item is None:
            for action in self.menu.actions():
                was = action.isEnabled()
                action.setEnabled(True)
                if thing.name == action.text():
                    action.setChecked(True)
                action.setEnabled(was)
        item = self.item_in_selected(thing)
        if item is None:
            item = ListThingItem(thing)
            self.selected_lw.addItem(item)


class ManageThings(QDialog, manage.Ui_Dialog):
    def __init__(self, controller, types, title='Редактировать препараты'):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(title)
        self.types = types

        self.controller = controller
        self.update_list()
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Ok).setText('Закрыть')
        self.delete_pb.clicked.connect(self.delete_clicked)
        self.add_pb.clicked.connect(self.add_clicked)
        self.listWidget.itemDoubleClicked.connect(self.thing_clicked)

    def thing_clicked(self, item):
        thing = item.thing
        thing_w = ThingDialog(self.controller, thing, readOnly=False, fixed_name=True)
        ret = thing_w.exec_()
        if ret != QDialog.Accepted:
            return
        dsc = thing_w.get_dsc()
        self.controller.update_dsc(thing, dsc)
        self.update_list()

    def delete_clicked(self):
        items = [index.row() for index in self.listWidget.selectedIndexes()]
        items.sort(reverse=True)
        for idx in items:
            thing = self.listWidget.item(idx).thing
            self.controller.remove_thing(thing)
        self.update_list()

    def add_clicked(self):
        thing_w = ThingDialog(self.controller, readOnly=False)
        ret = thing_w.exec_()
        if ret != QDialog.Accepted:
            return
        name = thing_w.get_name().strip()
        dsc = thing_w.get_dsc()
        if not name:
            msg = QMessageBox()
            msg.setWindowTitle('Ошибка')
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Название препарата не может быть пустым.')
            msg.exec_()
            return
        thing = self.controller.add_thing(name, dsc, self.types)
        if thing is None:
            msg = QMessageBox()
            msg.setWindowTitle('Ошибка')
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Препарат "{}" уже существует в Базе Данных'.format(name))
            msg.exec_()
            return
        ok_w = QMessageBox(QMessageBox.Information, 'Правило добавлено', 'Правило "{}" успешно добавлено.'.format(name), QMessageBox.Ok)
        ok_w.exec_()
        self.update_list()

    def update_list(self):
        self.listWidget.clear()
        for thing in self.controller.things(types=self.types):
            self.listWidget.addItem(ListThingItem(thing))


class ManageRules(QDialog, manage.Ui_Dialog):
    def __init__(self, controller):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Редактировать правила Базы Знаний')
        self.controller = controller

        self.update_list()
        self.buttonBox.accepted.connect(self.close)
        self.delete_pb.clicked.connect(self.delete_clicked)
        self.add_pb.clicked.connect(self.add_clicked)
        self.listWidget.itemDoubleClicked.connect(self.rule_clicked)

    def update_list(self):
        self.listWidget.clear()
        for rule in self.controller.rules():
            self.listWidget.addItem(ListRuleItem(rule))

    def delete_clicked(self):
        items = [index.row() for index in self.listWidget.selectedIndexes()]
        items.sort(reverse=True)
        for idx in items:
            rule = self.listWidget.item(idx).rule
            self.controller.remove_rule(rule)
        self.update_list()

    def add_clicked(self):
        rule_w = RuleDialog(self.controller, readOnly=False)
        ret = rule_w.exec_()
        if ret != QDialog.Accepted:
            return
        name = rule_w.get_name().strip()
        if not name:
            msg = QMessageBox()
            msg.setWindowTitle('Ошибка')
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Название правила не может быть пустым.')
            msg.exec_()
            return
        dsc = rule_w.get_dsc()
        things = rule_w.get_things()
        if len(things) < 1:
            msg = QMessageBox()
            msg.setWindowTitle('Ошибка')
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Правило должно содержать препараты.')
            msg.exec_()
            return
        self.controller.add_rule(name, dsc, things)
        ok_w = QMessageBox(QMessageBox.Information, 'Правило добавлено', 'Правило "{}" успешно добавлено.'.format(name), QMessageBox.Ok)
        ok_w.exec_()
        self.update_list()

    def rule_clicked(self, item):
        rule = item.rule
        rule_w = RuleDialog(self.controller, rule, readOnly=False)
        ret = rule_w.exec_()
        if ret != QDialog.Accepted:
            return
        name = rule_w.get_name()
        if not name:
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Ошибка')
            msg.setText('Название препарата не может быть пустым.')
            msg.exec_()
            return
        dsc = rule_w.get_dsc()
        things = rule_w.get_things()
        if len(things) < 1:
            msg = QMessageBox()
            msg.setWindowTitle('Ошибка')
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Правило должно содержать препараты.')
            msg.exec_()
            return
        self.controller.remove_rule(rule)
        self.controller.add_rule(name, dsc, things)
        self.update_list()
