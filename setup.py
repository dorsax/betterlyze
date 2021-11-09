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

def create_tables (connection,old_event,new_event):
    cursor = connection.cursor(buffered=True)
    print ("Creating tables if not existing...")
    cursor.execute ('''CREATE TABLE IF NOT EXISTS donations
                        (donated_at DATETIME, id VARCHAR(8), donated_amount_in_cents INT, page INT, event_id VARCHAR(8))''')
    cursor.execute ('''CREATE TABLE IF NOT EXISTS last_run
                        (created_at datetime, id VARCHAR(8), last_page INT, event_id VARCHAR(8))''')
    cursor.execute ('SELECT last_page FROM last_run WHERE event_id=%s',(old_event,))
    entry = cursor.fetchone()
    if entry is None:
        print("NO cached ENTRY FOUND, initializing the first ones.")
        cursor.execute("""INSERT INTO last_run
                        VALUES (NULL, NULL, 1,%s)""",(old_event,))
        connection.commit()
    cursor.execute ('''SELECT last_page FROM last_run where event_id=%s;''',(new_event,))
    entry = cursor.fetchone()
    if entry is None:
        print("NO cached ENTRY FOUND, initializing the first ones.")
        cursor.execute("""INSERT INTO last_run
                        VALUES (NULL, NULL, 1,%s)""",(new_event,))
        connection.commit()
    cursor.close()

if __name__ == '__main__':
    configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
    config = yaml.safe_load (configstream)
    address = config["database"].get('address')
    username = config["database"].get('username')
    password = config["database"].get('password')
    database = config["database"].get('database')
    oldevent = config["past_year"].get('event')
    newevent = config["current_year"].get('event')
    connection = create_connection(username=username,password=password,address=address,database=database)
    if connection is not None:
        # print ("Success")
        create_tables (connection,oldevent,newevent)
        connection.close()
