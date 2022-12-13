from keys import airtable_key, table_id # Выгружаем ключи из специально сгенерированного файла с ключами
from keys import airtable_salary_database_id, my_range

from pyairtable import Table

table = Table(airtable_key, airtable_salary_database_id, 'Название листа')

list1=[] # Столбцы данных
list2=[] 
list3=[] 


for i in table.all(fields=['Столбец1', 'Столбец2', 'Столбец3']):
  list1.append(i['fields']['Столбец1']) # Записываем информацию по признаку 1 для объекта
  list2.append(i['fields']['Столбец2']) # Записываем информацию по признаку 2 для объекта
  list3.append(i['fields']['Столбец3']) # Записываем информацию по признаку 3 для объекта

import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'key.json' # Ключ сервисного аккаунта в формате json
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) #Авторизация
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 

results = service.spreadsheets().values().batchUpdate(spreadsheetId = table_id, body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": my_range,
         "majorDimension": "COLUMNS",
         "values": [
                    list1, list2, list3 # Записываем данные по столбцам
                   ]}
    ]
}).execute()