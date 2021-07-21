from sqlite3.dbapi2 import connect
import yaml
import os
import sqlite3
from sqlite3 import Error

config_filename = 'config.yml'
def create_connection (db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    finally: 
        if connection:
            return connection

def create_tables (connection):
    cursor = connection.cursor()
    print ("Creating tables if not existing...")
    cursor.execute ('''CREATE TABLE IF NOT EXISTS donations
                        (created_at text, id text, donated_amount_in_cents text)''')
    cursor.execute ('''CREATE TABLE IF NOT EXISTS last_run
                        (created_at text, id text, last_page text)''')
    cursor.execute ('''SELECT rowid FROM last_run''')
    entry = cursor.fetchone()
    if entry is None:
        print("NO cached ENTRY FOUND, initializing the first one.")
        cursor.execute("""INSERT INTO last_run
                        VALUES ('', '', '-1')""")
        connection.commit()
    cursor.close()

if __name__ == '__main__':
    configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
    config = yaml.safe_load (configstream)
    db_file = config.get('database_name')
    connection = create_connection(db_file)
    if connection is not None:
        create_tables (connection)
        connection.close()
