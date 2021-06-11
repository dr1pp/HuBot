import sqlite3
from typing import List

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("data.db")
        self.cur = self.conn.cursor()
        self.setup_commands = []


    def execute(self, query: str, parameters=None):
        if parameters is None:
            self.cur.execute(query)
        else:
            self.cur.execute(query, parameters)
        self.save()


    def executemany(self, query: str, parameters):
        self.cur.execute(query, parameters)
        self.save()


    def get(self, query: str, parameters=None):
        self.execute(query, parameters)
        return self.cur.fetchall()


    def save(self):
        self.conn.commit()


    def initialize(self, commands: List[str]):
        self.setup_commands = commands
        for command in self.setup_commands:
            self.execute(command)


    def reset(self):
        self.cur.execute("""SELECT name 
                            FROM sqlite_master 
                            WHERE type = 'table' 
                            AND name NOT LIKE 'sqlite_%'""")
        names = self.cur.fetchall()
        for table_name in names:
            self.cur.execute("DROP TABLE ?", (table_name,))


