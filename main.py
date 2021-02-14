from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import os
import sys
import numpy as np
from numpy import *
import telebot
import configparser
import pymysql
import pickle
import json

config = configparser.ConfigParser()
config.read("settings.ini")
bot = telebot.TeleBot(config['Telegram']['token'])

CREDENTIALS_FILE = 'pizza-tg-bot-be9f47d83502.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_id = '1dJ2D_D5UqK-UOufyqApOPam3SLOWyCJ1CxQOZUZIAHU'

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
