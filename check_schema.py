import sqlite3
c = sqlite3.connect("enterprise.db")
for r in c.execute("select sql from sqlite_master where type='table'"):
    print(r[0])
    print()
