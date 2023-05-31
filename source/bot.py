import telebot
import tokens
import os
import db_work as db
from telebot import types

admin_chat  = tokens.admin_chat
token_bot = tokens.token_bot
db_path = db.db_path

print("Starting bot...")
bot = telebot.TeleBot(token_bot)
print("Ready!")

commands = {
    '/r':          'Создать заявку',
    '/ping':       'Проверить подключение',
    '/active':     'Список активных заявок',
    '/accept':     'Список принятых заявок',
    '/unaccept':   'Список непринятных заявок',
    '/kill':       'Выключить бота',
    '/msg':        'Отправка сообщения пользователю по заявке',
    '/track':      'Вход в чат',
    '/track_list': 'Списки чатов',
    '/untrack':    'Удаление чатов',
    '/export':     'Выгрузка файла базы данных',
    '/import':     'Загрузка файла базы данных',
}

rates = {
    '1': u'\U0001F621',
    '2': u'\U0001F612',
    '3': u'\U0001F610',
    '4': u'\U0001F604',
    '5': u'\U0001F44D'
}

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    if message.chat.id == admin_chat:
        menu=''
        kbd = types.ReplyKeyboardMarkup()
        buts = []
        for command in commands.keys():
            menu = f'{menu}{command}: {commands[command]}\n'
            buts.append(types.KeyboardButton(text=command))
        kbd.add(*buts)
        bot.send_message(admin_chat, menu, reply_markup=kbd)
    else:
        send_help_message_user(message)

def send_help_message_user(message):
    keyboard = types.ReplyKeyboardMarkup();
    key_accept = types.InlineKeyboardButton(text='Создать заявку', callback_data='create')
    keyboard.add(key_accept)
    bot.send_message(message.from_user.id, reply_markup=keyboard, text=f"Опишите свою проблему в чате. Для создания заявки нажмите кнопку Создать заявку")



track_list = {}

def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return k


@bot.message_handler(content_types=["text", "audio", "document", "photo", "video", "video_note", "voice", "location"])
def get_text_messages(message):
    # обработка только текстовых сообщений
    if message.content_type != 'text': return
    flag = False
    # Если сообщение от админа
    if message.chat.id == admin_chat:
        if message.text in ('/r', 'Создать заявку'):
            start_request(message)
        elif message.text == '/ping':
            bot.send_message(admin_chat, 'Бот активен')
        elif message.text == '/active':
            items=db.load_from_db(active=True)
            send_list_admin(items)
        elif message.text == '/accept':
            items=db.load_from_db(accept=True, active=True, logic="AND")
            send_list_admin(items)
        elif message.text == '/unaccept':
            items=db.load_from_db(accept=False, active=True, logic="AND")
            send_list_admin(items)
        elif message.text == '/track':
            create_track(message)
        elif message.text == '/untrack':
            del_track(message)
        elif message.text == '/track_list':
            send_track_list()
        elif message.text == '/msg':
            send_message_req(message)
        elif message.text == '/export':
            doc = open(db_path, 'rb')
            bot.send_document(admin_chat, doc)
            bot.send_document(admin_chat, "FILEID")
        elif message.text == '/import':
            bot.send_message(admin_chat, 'Прикрепите файл базы данных')
            bot.register_next_step_handler(message, load_db)
        elif message.text == '/kill':
            raise Exception('Turning off')
        return
    # Если чат отслеживается
    if message.from_user.id in track_list.values():
        flag = True
        bot.send_message(admin_chat, f'Чат заявки №{get_key(track_list, message.from_user.id)}:\n{message.text}')
    # Если сообщение от пользователя
    else:
        if message.text in ('/r', 'Создать заявку'):
            start_request(message)
        elif not flag:
            bot.send_message(message.from_user.id, text=f"Не могу распознать команду. Для помощи введите /help")

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == 'create':
        start_request(call.message)
    if 'rate' in call.data:
        set_rating(call)
    if call.message.chat.id == admin_chat:
        if 'accept' in call.data:
            accept_request(call)
        if call.data == "end":
            end_request(call)

# Отправка списка отслеживаемых
def send_track_list():
    if len(track_list) == 0:
        bot.send_message(admin_chat, 'Нету отслеживаемых чатов')
        return
    msg = f'Отслеживаемые чаты:\n'
    for item in track_list.keys():
        msg += item
        msg += ' '
    bot.send_message(admin_chat, msg)

# Создание отслеживаемого чата
def create_track(message):
    bot.send_message(admin_chat, 'Введите номер заявки')
    bot.register_next_step_handler(message, get_tracknum_cr)

def get_tracknum_cr(message):
    global track_list
    sender = db.get_sender_id(message.text)
    if (sender == None):
        bot.send_message(admin_chat, 'Такой заявки нету')
        return
    track_list[message.text]=sender
    bot.send_message(track_list[message.text], 'Системный администратор вошел в чат')
    bot.send_message(admin_chat, 'Просмотр чата начат')

# Удаление чата из отслеживаемых
def del_track(message):
    bot.send_message(admin_chat, 'Введите номер заявки')
    bot.register_next_step_handler(message, get_tracknum_del)

def get_tracknum_del(message):
    global track_list
    if message.text not in track_list.keys():
        bot.send_message(admin_chat, 'Такого чата нету')
        return
    # bot.send_message(track_list[message.text], 'Системный администратор вышел из чата')
    bot.send_message(admin_chat, 'Чат отключен')
    track_list.pop(message.text)

# Список заявок
def send_list_admin(items):
    if len(items) == 0:
        bot.send_message(admin_chat, 'Записей этой категории нет')
        return
    msg = ''
    for item in items:
        if len(item) == 0: continue
        msg += f'Заявка №{item[0]}\n'
        msg += f'{item[1]}\n'
        msg += f'{item[2]}\n'
        if item[4] == '1': msg += f'Принята\n\n'
        else: msg += f'Не принята\n\n'
    if len(msg)==0:
        bot.send_message(admin_chat, 'Таких заявок нету')
        return
    bot.send_message(admin_chat, msg)

# Отправка сообщения от админа по заявке /msg
req = ''
def send_message_req(message):
    bot.send_message(admin_chat, f'Введите номер заявки')
    bot.register_next_step_handler(message, get_msg_num_req)

def get_msg_num_req(message):
    global req
    if message.text not in track_list.keys():
        bot.send_message(admin_chat, 'Такого чата нету')
        return
    req = track_list[message.text]
    bot.send_message(admin_chat, 'Введите текст сообщения')
    bot.register_next_step_handler(message, get_msg_text_req)

def get_msg_text_req(message):
    text = message.text
    bot.send_message(req, text)

# Создание заявки в БД, команда /r
name=''
location=''
description=''
def start_request(message):
    bot.send_message(message.chat.id, text="Пожалуйста, представтесь", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    global name
    name = message.text
    bot.send_message(message.from_user.id, text="Где вы находитесь?")
    bot.register_next_step_handler(message, get_location)

def get_location(message):
    global location
    location = message.text
    bot.send_message(message.from_user.id, text='Кратко опишите проблему в одном сообщении. Можно прикрепить одно вложение.')
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    global description
    description = message.text
    create_request(message)

# Создание заявки в БД
def create_request(message):
    # Создание заявки в бд   
    # reply_markup=types.ReplyKeyboardRemove()
    new_request = db.new_request(description=description,
                                location=location,
                                sender=name,
                                date_start=message.date,
                                sender_id=message.from_user.id)
    # Отправка админу сообщения
    keyboard = types.InlineKeyboardMarkup()
    key_accept0 = types.InlineKeyboardButton(text='Принять: срочно',  callback_data='accept0') # кнопка "Принять"
    key_accept1 = types.InlineKeyboardButton(text='Принять: уже иду',  callback_data='accept1') # кнопка "Принять"
    key_accept2 = types.InlineKeyboardButton(text='Принять: в течении получаса',   callback_data='accept2') # кнопка "Принять"
    key_accept3 = types.InlineKeyboardButton(text='Принять: в течении дня',   callback_data='accept3') # кнопка "Принять"
    keyboard.add(key_accept0)
    keyboard.add(key_accept1)
    keyboard.add(key_accept2)
    keyboard.add(key_accept3)
    # Пересылка сообщения, если есть вложения в сообщении 
    if message.content_type != 'text':
        bot.forward_message(admin_chat, message.chat.id, message.id) 
    # Уведомление администраторов
    msg_to_admin = bot.send_message(admin_chat, text=f"Создана заявка №{new_request}:\n" + f'{name}; {location}; {description}', reply_markup=keyboard).id
    # добавление номера сообщения к заявке
    db.add_msg_admin(new_request, msg_to_admin)
    # Отправка ответа пользователю
    bot.send_message(message.from_user.id, text='Системный администратор рассмотрит вашу проблему в ближайшее время и ответит на неё')

def load_db(message):
    if (message.content_type!='document'):
        bot.send_message(admin_chat, 'Ошибка: необходимо прикрепить файл')
        return
    try:
        bot.send_message(admin_chat, 'Начинаем загрузку...')
        file_name = message.document.file_name
        if (str(file_name) != 'requests.db'): raise Exception('File name not requests.db')
        print ('File name: ' + file_name)
        print ('Downloading...')
        file_id = message.document.file_name
        file_id_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_id_info.file_path)
        p = os.getcwd()
        print ('Opening ' + '/' + db_path)
        if os.path.isfile(p + '/' + db_path):
            print('Deleting old DB')
            os.remove(p + '/' + db_path)
        print ('Writing ' + '/' + db_path)
        with open(p + '/' + db_path, 'wb') as new_db:
            new_db.write(downloaded_file)
        print ('Success!')
        bot.send_message(admin_chat, 'Загрузка базы данных выполнена')
    except Exception as e:
        print('Error while importing: ' + str(e))
        bot.send_message(admin_chat, 'Ошибка загрузки: ' + str(e))



def accept_request(call):
    # Изменения статуса на принятую
    priority=int(call.data[6])
    data = db.accept_request(call.message.id, priority)
    # Удаление клавиатуы с кнопками 'приянть...'
    bot.edit_message_reply_markup(admin_chat, message_id = call.message.id, reply_markup = '')
    # Отправка админу сообщения с завершением
    keyboard = types.InlineKeyboardMarkup()
    key_end = types.InlineKeyboardButton(text='Завершить', callback_data='end') # кнопка "Принять"
    keyboard.add(key_end)
    msg_end = bot.send_message(admin_chat, text=f"Заявка №{data[0]} принята. Завершить?", reply_markup=keyboard).id
    # Добавление сообщения с завершением
    db.add_msg_end(data[0], msg_end)
    # Отправка сообщения пользователю о принятии
    if call.data == 'accept0':
        bot.send_message(data[1], text='Системный администратор рассмотрел вашу проблему как срочную. Ожидайте его прибытия')
    elif call.data == 'accept1':
        bot.send_message(data[1], text='Ожидайте  прибытия системного администратора')
    elif call.data == 'accept2':
        bot.send_message(data[1], text='Системный администратор рассмотрел вашу проблему. К вам подойдут в течении получаса')
    elif call.data == 'accept3':
        bot.send_message(data[1], text='Системный администратор рассмотрел вашу проблему. Он прибудет к вам в течении дня')

def end_request(call):
    # Закрытие заявки
    request = db.set_msg_inactive(call.message.id)

    user_id = db.get_sender_id(request)
    # Удаление клавиатуры  с кнопкой 'завершить'
    bot.edit_message_reply_markup(admin_chat, message_id = call.message.id, reply_markup = '')

    # Отправление пользователю сообщения с запросом установить рейтинг
    keyboard = types.InlineKeyboardMarkup()
    but1=types.InlineKeyboardButton(text=rates['1'], callback_data='rate1')
    but2=types.InlineKeyboardButton(text=rates['2'], callback_data='rate2')
    but3=types.InlineKeyboardButton(text=rates['3'], callback_data='rate3')
    but4=types.InlineKeyboardButton(text=rates['4'], callback_data='rate4')
    but5=types.InlineKeyboardButton(text=rates['5'], callback_data='rate5')
    keyboard.add(but1, but2, but3, but4, but5)
    msg_user=bot.send_message(user_id, text='Оставьте отзыв о проделанной работе', reply_markup=keyboard)
    # Установка сообщения с рейтингом в БД
    db.set_rate_msg(request, msg_user.id)
    #  Отпралвление админу сообщения со временем
    dates = db.get_dates(request)
    bot.send_message(admin_chat, f"Заявка №{request} выполнена. Время на принятие: {dates[1]-dates[0]}. Общее время выполнения: {dates[2]-dates[0]}")
    # Сообщение пользователюю
    keyboard = types.ReplyKeyboardMarkup()
    key_accept = types.InlineKeyboardButton(text='Создать заявку', callback_data='create')
    keyboard.add(key_accept)
    bot.send_message(user_id, reply_markup=keyboard, text=f"Опишите свою проблему в чате. Для создания заявки нажмите кнопку Создать заявку")

def set_rating(call):
    # Удаление клавиатуры с отзывами
    rate = call.data[4]
    bot.edit_message_reply_markup(call.message.chat.id, message_id = call.message.id, reply_markup = '')
    bot.edit_message_text(text=f'Спасибо за отзыв! Вы поставили ' + rates[rate], chat_id=call.message.chat.id, message_id=call.message.id)
    req = db.set_rating(call.message.chat.id, call.message.id, rate)
    bot.send_message(admin_chat, f'Рейтинг заявки №{req}: {rate}')



# Подключение бота
# bot.send_message(admin_chat, 'Бот запущен!')
try:
    bot.infinity_polling()
except SystemExit  as e:
    bot.send_message(admin_chat, 'Бот выключен')
except Exception as e:
    bot.send_message(admin_chat, f'Бот выключен: {e}')
    print(e)
input()
