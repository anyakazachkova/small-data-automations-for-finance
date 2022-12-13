import requests
import json
from datetime import datetime

from keys import finolog_key, id1, id2, finolog_url, range_name # Выгружаем ключ и другие нужные переменные

current_datetime = datetime.now()

params = {'from' : '2022-01-01',       # Параметры выгружаемых данных
          'to' : '2022-12-31',
          'group' : 'category',
          'with_vat' : 'true',
          'interval_grouping_type' : 'month',
          'with_planned' : 'true',
          'base_currency' : 'true'
      } 

url = finolog_url
r = requests.get(url, params, headers={'api-token': finolog_key})

pl_by_category = json.loads(r.text)

month = current_datetime.month

window_start = month - 3
window_end = month - 1 # Это всегда будет последний закрытый месяц

revenue = 0
overhead_cost = 0

l = [1, 2, 3, 7, 13, 14, 15, 16, 17, 19] # Список категорий для косвенных расходов - меняется, если происходят изменения в струткуре данных

for n in l: # Обращаемся к списку категорий косвенных расходов; n - категория
  for i in pl_by_category['category'][n]['outcomes']: # Обращаемся к расходной части этих статей; i - обозначение месяца
    if window_start <= int(i[-2:]) <= window_end: # Условием ограничеваем временной интервал для суммирования
      for j in pl_by_category['category'][n]['outcomes'][i]: # Заходим в каждый месяц и берем величину в базовой валюте (всегда все переведено в рубли)
        overhead_cost += j['base_value'] # Добавляем величину расходов к общей переменной


for i in pl_by_category['category'][21]['incomes']: # Обращаемся к статье Доход к доходной части; i - обозначение месяца
  if window_start <= int(i[-2:]) <= window_end: # Условием ограничиваем временной интервал для суммирования
    for j in pl_by_category['category'][21]['incomes'][i]: # Заходим в каждый месяц и берем значение в базовой валюте
      revenue += j['base_value'] # Добавляем величину к общей переменной


overhead = -1 * overhead_cost / revenue # Считаем коэффициент накладных расходов как пропорция в выручке


import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'key.json' # Ключ сервисного аккаунта в формате json
# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) # Авторизация
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 


project_calculator_id = [id1, 
                         id2] # id таблиц

for i in project_calculator_id: # Записываем простым циклов одно и то же значение в обе таблицы
  results = service.spreadsheets().values().batchUpdate(spreadsheetId = i, body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": range_name,
         "majorDimension": "ROWS",     
         "values": [
                    [round(overhead, 2)] # Записываем коэффициент косенных расходов
                   ]}
            ]
    }).execute()