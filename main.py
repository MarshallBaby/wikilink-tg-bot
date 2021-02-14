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
from googleapiclient.discovery import build
# from classes import Statement

#-----CLASS AREA-------

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
        sql = "UPDATE `temp` SET `statement` = " + str(value) + " WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        connection.commit()
       
    def reset(self, message):
        global connection
        chat_id = message.chat.id
        sql = "UPDATE `temp` SET `statement` = 0, `level` = -1, `data_array` = '' WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        connection.commit()
        
    def motion(self, statement, message):
        if(statement == 0):
            motion.free(message)
        elif(statement == 1):
            motion.collect(message)
            
class Motion:
    def free(self, message):
        bsm(message, "Нечего делать")
    def collect(self, message):
        pprint(level.check(message))   
            
class Level:
    def check(self, message):
        global connection
        chat_id = message.chat.id
        connection.commit()
        sql = "SELECT `level` FROM `temp` WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        res = cursor.fetchone()[0]
        return res  
            
#-----END CLASS AREA-------
    

config = configparser.ConfigParser()
config.read("settings.ini")
bot = telebot.TeleBot(config['Telegram']['token'])

CREDENTIALS_FILE = 'wikilink-tg-bot-9b4dfdea490b.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_id = '1dJ2D_D5UqK-UOufyqApOPam3SLOWyCJ1CxQOZUZIAHU'

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = build('sheets', 'v4', http=httpAuth)

global connection
connection = pymysql.connect(
    host= config['SQL']['host'],
    user= config['SQL']['user'],
    password= config['SQL']['password'],
    charset= config['SQL']['charset'],
    db= config['SQL']['db'],
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
    
@bot.message_handler(commands=['help'])
def help_reaction(message):
    bot.send_message(message.chat.id, config['Bot']['help_reply_text'])
    
statement = Statement() 
motion = Motion()
level = Level()
    
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
        cursor.execute(sql, (chat_id, chat_username, chat_name, chat_lastname, 0, -1, ""))
        connection.commit()
    bot.send_message(message.chat.id, config['Bot']['start_reply_text'])
    
    
@bot.message_handler(commands=['new'])
def new_reaction(message):
    if(statement.check(message) == 0):
        statement.upload(message, 1)
        statement.motion(statement.check(message), message)
    else:
        statement.reset(message)
        bsm(message, config['Bot']['break_reply_text'])
        
        
@bot.message_handler(content_types=['text'])
def text_reaction(message):
    statement.motion(statement.check(message), message)   
        
bot.polling()
