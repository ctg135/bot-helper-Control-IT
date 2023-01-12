import sqlite3
import datetime
from datetime import datetime
#
# Сущности базы данных
#
# id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
# description   TEXT    DEFAULT '0',
# sender        TEXT    DEFAULT '0',
# location      TEXT    DEFAULT '0',
# date_start    TEXT    DEFAULT '0',   
# date_accept   TEXT    DEFAULT '0',
# date_end      TEXT    DEFAULT '0',
# sender_id     INTEGER DEFAULT 0,
# rating        INTEGER DEFAULT 0,
# priority      INTEGER DEFAULT 0,
# accepted      BOOL    DEFAULT 0,   
# active        BOOL    DEFAULT 1,
# msg_to_admin  INTEGER DEFAULT 0,
# msg_end       INTEGER DEFAULT 0,
# msg_u_rate    INTEGER DEFAULT 0

# CHECK | |
# Записывает начальную заявку 
# return Номер заявки
db_path = 'db/requests.db'

def new_request(description, date_start, sender_id, sender, location):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"INSERT INTO requests (description, date_start, sender_id, sender, location, active) VALUES (\"{description}\", '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', {sender_id}, \"{sender}\", \"{location}\", 1)"
    data =                      (description, datetime.now(), sender_id, sender, location, True)
    cursor.execute(sql)
    conn.commit()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql1 = f"SELECT id FROM requests ORDER BY id DESC"
    data = cursor.execute(sql1)
    print(data)
    for row in data:
        return row[0]

# Добавляет номер сообщения админа
def add_msg_admin(request_id, msg_to_admin_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"UPDATE requests SET msg_to_admin = {msg_to_admin_id} WHERE id = {request_id} "
    cursor.execute(sql)
    conn.commit()

# priority - 
# 0 - срочно
# 1 - быстро
# 2 - медленно
# 3 - в течении дня
# return [0] - id заявки, [1] - id пользователя
def accept_request(msg_to_admin, priority):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Поиск id заявки и пользователя
    sql = f"SELECT id, sender_id FROM requests WHERE msg_to_admin = {msg_to_admin}"
    data = cursor.execute(sql)
    req_id = 0
    sender_id = 0
    for row in data:
        req_id = row[0]
        sender_id = row[1]
        break
    # Установка заявки принятой
    sql = f"UPDATE requests SET accepted = {True}, priority={priority}, date_accept='{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}' WHERE id = {req_id}"
    cursor.execute(sql)
    conn.commit()
    return (req_id, sender_id)

# Добавление сообщения с заврешением
def add_msg_end(request, msg_end):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"UPDATE requests SET msg_end = {msg_end} WHERE id = {request}"
    cursor.execute(sql)
    conn.commit()

def set_msg_inactive(msg_end):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"SELECT id FROM requests WHERE msg_end = {msg_end}"
    data = cursor.execute(sql)
    request = 0
    for row in data:
        request = row[0]
        break
    # Обновление записи
    sql = f"UPDATE requests SET active = {False}, date_end='{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}' WHERE id = {request}"
    cursor.execute(sql)
    conn.commit()
    return request

# Функция выгрузки всех данных из БД
# Переделать на обработку сырых данных
def load_from_db(active: bool=False, accept: bool=False, logic: str="OR"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"SELECT * FROM requests WHERE accepted = {accept} {logic} active = {active}"
    data = cursor.execute(sql)
    items = [[],[]]
    for row in data:
        temp = []
        for col in row:
            temp.append(str(col))
        items.append(temp)
    return items

# CHECK | |
# Получение отправителя по заявке или None
# return sender_id: int
def get_sender_id(request):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"SELECT sender_id FROM requests WHERE id = {request}"
    data = cursor.execute(sql)
    for row in data:
        return row[0]
    return None

# Установка сообщения с рейтингом
def set_rate_msg(request, message_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = f"UPDATE requests SET msg_u_rate={message_id} WHERE id={request}"
    cursor.execute(sql)
    conn.commit()
    
# Установка рейтинга
def set_rating(sender_id, msg_rate, rate):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    sql = f"UPDATE requests SET rating={rate} WHERE msg_u_rate={msg_rate} AND sender_id={sender_id}"
    cursor.execute(sql)
    conn.commit()
    
    sql = f"SELECT id FROM requests WHERE msg_u_rate='{msg_rate}' AND sender_id={sender_id}"
    data = cursor.execute(sql)
    for row in data:
        return row[0]
    return None

# Получение дат
# return: (date, date, date)
def get_dates(request):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    sql = f"SELECT date_start, date_accept, date_end FROM requests WHERE id={request}"
    cursor.execute(sql)
    
    data = cursor.execute(sql)
    for row in data:
        return (datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'), datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'), datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S'))
    return None