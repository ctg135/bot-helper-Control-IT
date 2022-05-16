import sqlite3

def start_func():
    help_msg="""Comands for DB control:

-init - Starts DataBase
-drop - Drops tables
-sql  - Input querry to database
-exit - Exit from program
"""
    print(help_msg)
    while True:
        command = input('Enter command: ')
        if command=='-exit':
            break
        elif command=='-sql':
            sql_querry()
        elif command=='-init':
            init_db()
        elif command=='-drop':
            drop_db()
        elif command in ('-help', '-?', '-h'):
            print(help_msg)

def init_db():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE requests
                     (id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                      description   TEXT    DEFAULT '0',
                      sender        TEXT    DEFAULT '0',
                      location      TEXT    DEFAULT '0',
                      date_start    TEXT    DEFAULT '0',   
                      date_accept   TEXT    DEFAULT '0',
                      date_end      TEXT    DEFAULT '0',
                      sender_id     INTEGER DEFAULT 0,
                      rating        INTEGER DEFAULT 0,
                      priority      INTEGER DEFAULT 0,
                      accepted      BOOL    DEFAULT 0,   
                      active        BOOL    DEFAULT 0,
                      msg_to_admin  INTEGER DEFAULT 0,
                      msg_end       INTEGER DEFAULT 0,
                      msg_u_rate    INTEGER DEFAULT 0
                      )""")
    conn.commit()
    print('DB Initiated')
    
def drop_db(): # SECURE!
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE requests")
    conn.commit()
    print('Dropped')

def sql_querry(): # SECURE!
    sql = input('Input SQL-command:\n')
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    try:
        data = cursor.execute(sql)
        print_table(data)
        conn.commit()
        input('Press enter to continue')
    except sqlite3.OperationalError as e:
        print(f'Querry error: {e}')
        input('Press enter to continue')

def print_table(items):
    print('Result:')
    i=0
    for row in items:
        i = i + 1
        print(f'  #{i}')
        for col in row:
            print(str(col))
    print(f'\nTotal rows: {i}\n')


start_func()