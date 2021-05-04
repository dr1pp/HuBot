import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("data.db")
        self.cur = self.conn.cursor()


    def execute(self, query, parameters=None):
        if parameters is None:
            self.cur.execute(query)
        else:
            self.cur.execute(query, parameters)
        self.save()


    def executemany(self, query, parameters):
        self.cur.execute(query, parameters)
        self.save()


    def get(self, query, parameters=None):
        self.execute(query, parameters)
        return self.cur.fetchall()


    def save(self):
        self.conn.commit()