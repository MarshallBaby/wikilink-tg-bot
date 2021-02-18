import oauth2client
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from pprint import pprint
import os
import sys
import numpy as np
from numpy import *
import telebot
import configparser
import pymysql
import json
from datetime import date
from googleapiclient.discovery import build
# from classes import Statement

# -----CLASS AREA-------


class Statement:
    def check(self, message):
        global connection
        chat_id = message.chat.id
        connection.commit()
        sql = "SELECT `statement` FROM `temp` WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        res = cursor.fetchone()[0]
        return res

    def upload(self, message, value):
        global connection
        chat_id = message.chat.id
        sql = "UPDATE `temp` SET `statement` = " + \
            str(value) + " WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        connection.commit()

    def reset(self, message):
        global connection
        chat_id = message.chat.id
        sql = "UPDATE `temp` SET `statement` = 0, `level` = -1, `data_array` = '' WHERE `id` = " + \
            str(chat_id)
        cursor.execute(sql)
        connection.commit()

    def motion(self, statement, message):
        if(statement == 0):
            motion.free(message)
        elif(statement == 1):
            motion.collect(message)
        elif(statement == 2):
            motion.readbydate(message)


class Motion:
    def free(self, message):
        bsm(message, "Нечего делать")

    def collect(self, message):
        if(level.check(message) == -1):
            bsm(message, config['Bot']['start_new_reply_text'])
            data_array = []
            for i in range(table.feild_amount):
                data_array.append("?")
            data_array = str("#".join(data_array))
            data_array_obj.upload(message, data_array)
            level.upload(message, level.check(message) + 1)
            bsm(message, "Введите знач " + str(level.check(message)))
        else:
            data_array = data_array_obj.get(message)  # получаем str
            data_array = data_array.split("#")  # делим на массив
            data_array[level.check(message)] = message.text  # заменяем
            data_array = str("#".join(data_array))  # собираем
            data_array_obj.upload(message, data_array)  # отправляем
            level.upload(message, level.check(message) + 1)
            if(level.check(message) != table.feild_amount):
                bsm(message, "Введите знач " + str(level.check(message)))
        if(level.check(message) == table.feild_amount):
            data_array = data_array_obj.get(message)
            data_array = data_array.split("#")
            value_range_body = {
                "values": [
                    data_array
                ]
            }
            request = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Лист1!A1:E1',
                valueInputOption='USER_ENTERED',
                body=value_range_body,
            )
            response = request.execute()
            bsm(message, "Отправляем массив")
            statement.reset(message)

    def readbydate(self, message):
        global agent_field_num
        if(level.check(message) == -1):
            bsm(message, config['Bot']['choose_your_fighter_reply'])
            level.upload(message, level.check(message) + 1)
        else:
            agent_name = message.text
            request_body = {
                "dataFilters": [
                    {
                        "gridRange": {
                            "sheetId": int(config['Google']['sheet_id']),
                            "startColumnIndex": agent_field_num,
                            "endColumnIndex": agent_field_num + 1,
                            "startRowIndex": 1
                        }
                    }
                ],
                "majorDimension": "COLUMNS",
                "valueRenderOption": "FORMATTED_VALUE"
            }
            request = service.spreadsheets().values().batchGetByDataFilter(
                spreadsheetId=spreadsheet_id,
                body=request_body,

            ).execute()
            agent_array = request.get("valueRanges")[0].get('valueRange').get('values')[0]
            pprint(agent_array)
            request_body = {
                "dataFilters": [
                    {
                        "gridRange": {
                            "sheetId": int(config['Google']['sheet_id']),
                            "startColumnIndex": date_table_num,
                            "endColumnIndex": date_table_num + 1,
                            "startRowIndex": 1
                        }
                    }
                ],
                "majorDimension": "COLUMNS",
                "valueRenderOption": "FORMATTED_VALUE"
            }
            request = service.spreadsheets().values().batchGetByDataFilter(
                spreadsheetId=spreadsheet_id,
                body=request_body,

            ).execute()
            date_array = request.get("valueRanges")[0].get('valueRange').get('values')[0]
            pprint(date_array)
            
            for i in range(len(agent_array)):
                if(date_array[i] == str(date.today().strftime("%d.%m.%Y")) and agent_array[i] == message.text):
                    pprint("Match!")
            statement.reset(message)


class Level:
    def check(self, message):
        global connection
        chat_id = message.chat.id
        connection.commit()
        sql = "SELECT `level` FROM `temp` WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        res = cursor.fetchone()[0]
        return res

    def upload(self, message, value):
        global connection
        chat_id = message.chat.id
        sql = "UPDATE `temp` SET `level` = " + \
            str(value) + " WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        connection.commit()


class Data_Array:
    def get(self, message):
        global connection
        chat_id = message.chat.id
        connection.commit()
        sql = "SELECT `data_array` FROM `temp` WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        res = cursor.fetchone()[0]
        return res

    def upload(self, message, value):
        global connection
        chat_id = message.chat.id
        sql = "UPDATE `temp` SET `data_array` = '" + \
            str(value) + "' WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        connection.commit()

    def erase(self, message):
        global connection
        chat_id = message.chat.id
        sql = "UPDATE `temp` SET `data_array` = '' WHERE `id` = " + \
            str(chat_id)
        cursor.execute(sql)
        connection.commit()


class Table:
    def __init__(self, field_amount):
        self.feild_amount = field_amount

# -----END CLASS AREA-------


config = configparser.ConfigParser()
config.read("settings.ini")
bot = telebot.TeleBot(config['Telegram']['token'])

CREDENTIALS_FILE = 'wikilink-tg-bot-9b4dfdea490b.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_id = config['Google']['spreadsheet_id']

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)

result = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='Лист1!A1:Z1',
    # dateTimeRenderOption = 'FORMATTED_STRING',
    # majorDimension = 'DIMENTION_UNSPECIFIED'
).execute()
rows = result.get('values', [])
# -----Получаем номера полей-------
global agent_field_num
global date_table_num

for i in range(len(rows[0])):
    if(str(rows[0][i]) == config['Google']['alent_table_name']):
        agent_field_num = i
    elif(str(rows[0][i]) == config['Google']['date_table_name']):
        date_table_num = i

global connection
connection = pymysql.connect(
    host=config['SQL']['host'],
    user=config['SQL']['user'],
    password=config['SQL']['password'],
    charset=config['SQL']['charset'],
    db=config['SQL']['db'],
)

cursor = connection.cursor()

# SQL проверка подключения
if connection.open != 1:
    print("SQL connection ERROR")
    sys.exit()
else:
    print("SQL connected sucsessfully")


def bsm(message, value):
    bot.send_message(message.chat.id, value)


def text_checker(message):
    return message.text.find('#')


@bot.message_handler(commands=['help'])
def help_reaction(message):
    bot.send_message(message.chat.id, config['Bot']['help_reply_text'])


statement = Statement()
motion = Motion()
level = Level()
data_array_obj = Data_Array()
table = Table(len(rows[0]))


@bot.message_handler(commands=['start'])
def user_registration(message):
    chat_id = message.chat.id
    sql = "SELECT * FROM `temp` WHERE `id` = " + \
        str(message.chat.id)
    cursor.execute(sql)
    res = cursor.fetchall()
    if (res == ()):
        chat_username = str(message.chat.username)
        chat_name = str(message.chat.first_name)
        chat_lastname = str(message.chat.last_name)
        sql = "INSERT INTO `temp` (`id`, `username`, `name`, `lastname`, `statement`, `level`, `data_array`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (chat_id, chat_username,
                             chat_name, chat_lastname, 0, -1, ""))
        connection.commit()
    bot.send_message(message.chat.id, config['Bot']['start_reply_text'])


# @bot.message_handler(commands=['new'])
# def new_reaction(message):
#     if(statement.check(message) == 0):
#         statement.upload(message, 1)
#         statement.motion(statement.check(message), message)
#     else:
#         statement.reset(message)
#         bsm(message, config['Bot']['break_reply_text'])

@bot.message_handler(commands=['today'])
def new_reaction(message):
    if(statement.check(message) == 0):
        statement.upload(message, 2)
        statement.motion(statement.check(message), message)
    else:
        statement.reset(message)
        bsm(message, config['Bot']['break_reply_text'])


@bot.message_handler(content_types=['text'])
def text_reaction(message):
    if(text_checker(message) == -1):
        statement.motion(statement.check(message), message)
    else:
        bsm(message, config['Bot']['sharp_error_reply_text'])


bot.polling()
