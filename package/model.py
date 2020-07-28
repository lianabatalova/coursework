from PyQt5.QtSql import (
    QSqlDatabase,
    QSqlQuery,
    QSqlTableModel,
    QSqlQueryModel,
)
import sys
import itertools
import ast


USER        = 'medicine'
PASSWORD    = 'medicine'
DB_NAME     = 'medicine'
HOSTNAME    = 'localhost'
PORT        = '5432'


def combinations(iterable, r = None):
    if r is not None:
        return itertools.combinations(iterable, r)
    result = []
    for l in range(0, len(iterable) + 1):
        result.extend(itertools.combinations(iterable, l))
    return result


class Rule:
    def __init__(self, idx=None, name=None, things=None, dsc=None):
        self.idx = idx
        self.name = name
        self.things = things
        if things is not None:
            things.sort(key=lambda thing: thing.idx)
        self.dsc = dsc

    def __eq__(self, other):
        if not isinstance(other, Rule):
            return False
        return self.idx == other.idx and \
               self.name == other.name and \
               self.t_ids == other.t_ids and \
               self.dsc == other.dsc


class Thing:
    def __init__(self, idx=None, name=None, dsc=None):
        self.idx = idx
        self.name = name
        self.dsc = dsc

    def __eq__(self, other):
        if not isinstance(other, Thing):
            return False
        return self.idx == other.idx and \
               self.name == other.name and \
               self.dsc == other.dsc


def _array_string(array):
    return 'ARRAY[' + ','.join(str(x) for x in array) + ']::integer[]'


class Database:
    def __init__(self):
        self.db = QSqlDatabase.addDatabase("QPSQL")
        self.db.setHostName(HOSTNAME)
        self.db.setPort(int(PORT))
        self.db.setDatabaseName(DB_NAME)
        self.db.setUserName(USER)
        self.db.setPassword(PASSWORD)
        if not self.db.open():
            raise Exception(self.db.lastError().text())

    def rules_by_tids(self, t_ids, exact):
        query = QSqlQueryModel()
        if exact:
            query.setQuery("select * from rules "\
                           "where things={}"\
                               .format(_array_string(t_ids)),
                           db=self.db)
        else:
            query.setQuery("select * from rules "\
                           "where things @>{}"\
                               .format(_array_string(t_ids)),
                           db=self.db)
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)
        ret = []
        for i in range(query.rowCount()):
            rule = self.rule_by_sqlrecord(query.record(i))
            ret.append(rule)
        return ret

    def thing_by_name(self, name):
        query = QSqlQueryModel()
        query.setQuery("select * from things "\
                       "where name='{}'"\
                           .format(name),
                       db=self.db)
        if query.rowCount() == 0:
            return None
        return self.thing_by_sqlrecord(query.record(0))

    def thing_by_id(self, idx):
        query = QSqlQueryModel()
        query.setQuery("select * from things "\
                       "where id={}"\
                           .format(idx),
                       db=self.db)
        if query.rowCount() == 0:
            return None
        return self.thing_by_sqlrecord(query.record(0))

    def insert_thing(self, name, dsc, types):
        if self.thing_by_name(name) != None:
            print('Thing {} already exist', name)
            return None
        query = QSqlQueryModel()
        query.setQuery("insert into things(name, dsc, type) "\
                       "values ('{}', '{}', '{}')"\
                           .format(name, dsc, types))
        return self.thing_by_name(name)

    def insert_rule(self, name, dsc, things):
        query = QSqlQueryModel()
        t_ids = sorted([x.idx for x in things])
        query.setQuery("insert into rules(name, things, dsc) "\
                       "values ('{}', {}, '{}')"\
                           .format(name,
                                   _array_string(t_ids),
                                   dsc))
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)

    def table(self, name, types):
        table = QSqlTableModel(db=self.db)
        table.setTable(name)
        if types is not None:
            table.setFilter('type=ANY({})'.format(_array_string(types)))
        table.select()
        return table

    def rule_by_sqlrecord(self, record):
        rule = Rule()
        rule.idx = record.value('id')
        rule.dsc = record.value('dsc')
        rule.name = record.value('name')
        rule.things = []
        tids = ast.literal_eval(record.value('things'))
        for idx in tids:
            rule.things.append(self.thing_by_id(idx))
        return rule

    def thing_by_sqlrecord(self, record):
        thing = Thing()
        thing.idx = record.value('id')
        thing.dsc = record.value('dsc')
        thing.name = record.value('name')
        return thing

    def remove_rule(self, rule):
        query = QSqlQueryModel()
        query.setQuery("delete from rules "\
                       "where id={}"\
                           .format(rule.idx))
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)

    def rules_with_thing(self, thing):
        query = QSqlQueryModel()
        query.setQuery("select * from rules "\
                       "where {} = ANY(things)"\
                            .format(thing.idx))
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)
        ret = []
        for i in range(query.rowCount()):
            rule = self.rule_by_sqlrecord(query.record(i))
            ret.append(rule)
        return ret

    def remove_thing(self, thing):
        rules = self.rules_with_thing(thing)
        for rule in rules:
            self.remove_rule(rule)
        query = QSqlQueryModel()
        query.setQuery("delete from things "\
                       "where id={}"\
                            .format(thing.idx))
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)

    def things(self, types):
        query = QSqlQueryModel()
        if types is not None:
            query.setQuery("select * from things "\
                           "where type=ANY({})"\
                               .format(_array_string(types)))
        else:
            query.setQuery("select * from things")
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)
        ret = []
        for i in range(query.rowCount()):
            thing = self.thing_by_sqlrecord(query.record(i))
            ret.append(thing)
        return ret

    def rules(self):
        query = QSqlQueryModel()
        query.setQuery("select * from rules")
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)
        ret = []
        for i in range(query.rowCount()):
            rule = self.rule_by_sqlrecord(query.record(i))
            ret.append(rule)
        return ret

    def update_dsc(self, thing, dsc):
        query = QSqlQueryModel()
        query.setQuery("UPDATE things "\
                       "SET dsc = '{}' "\
                       "WHERE id={}"
                            .format(dsc, thing.idx))
        if query.lastError().isValid():
            print(query.lastError().text(), file=sys.stderr)


class Model:
    def __init__(self):
        self.db = Database()

    def qsql_table_model(self, tablename, types):
        return self.db.table(tablename, types)

    def analysis_ids(self, t_ids, exact=True):
        ret = []
        t_ids.sort()
        for dc in combinations(t_ids):
            ret.extend(self.db.rules_by_tids(dc, exact))
        return ret

    def analysis(self, things, exact=True):
        ret = []
        t_ids = [thing.idx for thing in things]
        return self.analysis_ids(t_ids, exact)

    def add_thing(self, name, dsc, types):
        return self.db.insert_thing(name, dsc, types)

    def add_rule(self, name, dsc, things):
        return self.db.insert_rule(name, dsc, things)

    def thing_by_name(self, name):
        return self.db.thing_by_name(name)

    def remove_rule(self, rule):
        self.db.remove_rule(rule)

    def remove_thing(self, thing):
        self.db.remove_thing(thing)

    def things(self, types=None):
        if isinstance(types, int):
            types = [types]
        return self.db.things(types)

    def rules(self):
        return self.db.rules()

    def update_dsc(self, thing, dsc):
        return self.db.update_dsc(thing, dsc)
