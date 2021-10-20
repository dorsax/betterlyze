from sqlite3.dbapi2 import connect
import yaml
import os
import mysql.connector
from sqlite3 import Error

config_filename = 'config.yml'
def create_connection (address,username,password,database):
    connection = None
    try:
        connection = mysql.connector.connect(host=address,user=username,password=password,database=database)
    except Error as e:
        print(e)
    finally: 
        if connection:
            return connection

def create_tables (connection):
    cursor = connection.cursor()
    print ("Creating tables if not existing...")
    cursor.execute ('''CREATE TABLE IF NOT EXISTS donations
                        (donated_at DATETIME, id VARCHAR(8), donated_amount_in_cents INT, page INT)''')
    cursor.execute ('''CREATE TABLE IF NOT EXISTS last_run
                        (created_at datetime, id VARCHAR(8), last_page INT)''')
    cursor.execute ('''SELECT last_page FROM last_run''')
    entry = cursor.fetchone()
    if entry is None:
        print("NO cached ENTRY FOUND, initializing the first one.")
        cursor.execute("""INSERT INTO last_run
                        VALUES (NULL, NULL, 1)""")
        connection.commit()
    cursor.close()

if __name__ == '__main__':
    configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
    config = yaml.safe_load (configstream)
    address = config["database"].get('address')
    username = config["database"].get('username')
    password = config["database"].get('password')
    database = config["database"].get('database')
    connection = create_connection(username=username,password=password,address=address,database=database)
    if connection is not None:
        # print ("Success")
        create_tables (connection)
        connection.close()
