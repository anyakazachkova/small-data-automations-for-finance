import requests
import json
from pprint import pprint
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from pandas import read_csv, DataFrame
import seaborn as sns

# Специальные библиотеки для работы с Гугл Драйв
import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import time

# Ключи
from keys import notion_token, range1, range2, table_id, block_url # Ключ и другие нужные переменные

# Специальные библиотеки для работы с notion
from notion.block import ImageBlock
from notion.client import NotionClient

"""# Часть 1: Выгрузка нужных цифр из Google

##1.1 Авторизация
"""

CREDENTIALS_FILE = 'key.json' #  Ключ сервисного аккаунта в формате json

#  Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) #  Авторизация
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) #  Выбираем работу с таблицами и 4 версию API

"""##1.2 Собираем данные

Нас интересуют:
* Изменение ячейки **В1**
* Сбор информации **С1:Q1** и **С4:Q4**
"""

# Цифры выгружаются в формате с разделителями, поэтому надо привести все к формату int

# Напишем функцию для обработки формата и заодно перевода чисел в тысячи
def to_int(element):
  return int(element.replace('\xa0', ''))/1000

scenario = ['first', 'second', 'third'] #  Какие есть сценарии для обновления расчетов
ranges_income = range1 #  Откуда берем данные по выручке и даты
ranges_balance = range2 #  Откуда берем данные по денежным балансам

revenue_data = pd.DataFrame() #  Будем заполнять один датафрейм для выручки
cash_data = pd.DataFrame() #  И другой для денежных остатков

for var in scenario:
  results = service.spreadsheets().values().batchUpdate(spreadsheetId = table_id, body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": "CashFlow!B1",
         "majorDimension": "ROWS",     
         "values": [
                    [var] #Записываем название сценария
                   ]}
            ]
    }).execute()

  results = service.spreadsheets().values().batchGet(spreadsheetId = table_id, 
                                     ranges = ranges_income, 
                                     valueRenderOption = 'FORMATTED_VALUE',  
                                     dateTimeRenderOption = 'FORMATTED_STRING').execute() 
    
  income_values = results['valueRanges'][0]['values']

  results = service.spreadsheets().values().batchGet(spreadsheetId = table_id, 
                                     ranges = ranges_balance, 
                                     valueRenderOption = 'FORMATTED_VALUE',  
                                     dateTimeRenderOption = 'FORMATTED_STRING').execute() 
  balance_values = results['valueRanges'][0]['values']

  # Выделяем строку с датами
  dates = income_values[0]

  # Применяем обработку формата к выручке и балансам
  income_values = list(map(to_int, income_values[-1]))
  balance_values = list(map(to_int, balance_values[0]))

  # Добавляем столбцы в датафреймы
  revenue_data[var] = income_values
  cash_data[var] = balance_values

# Добавляем даты как индекс
revenue_data.index = dates
cash_data.index = dates

"""# Часть 2: Строим графики"""

# График выручки

fig, ax = plt.subplots()

x = revenue_data.index
y1 = revenue_data['first']
y2 = revenue_data['second']
y3 = revenue_data['third']

col1 = "#FA8072"
col2 = "#CD853F"
col3 = "#FFD700"
col4 = "#F4A460"
col5 = "#8FBC8F"

ax.bar(x, y3, label='first', color = col1, alpha=0.9)
ax.bar(x, y2, label='second', color = col3, alpha=0.8)
ax.bar(x, y1, label='third', color = col2, alpha=0.6)

for i in range(len(y1)):
  plt.annotate(y1[i], (i-0.5, y1[i]))
  plt.annotate(y2[i], (i-0.5, y2[i]))
  plt.annotate(y3[i], (i-0.5, y3[i]))

fig.set_figwidth(15)    
fig.set_figheight(9)    
fig.set_facecolor('floralwhite')
ax.set_facecolor('seashell')
plt.xticks(rotation=50)
ax.set_xlabel('месяц', fontsize=20)
ax.set_ylabel('тыс. руб.', fontsize=20)
ax.set_title("Прогноз выручки", fontsize=18)
ax.legend(fontsize=10)

plt.grid(linestyle='--', alpha=0.5)
plt.savefig('revenue.jpg')
plt.show()

# График денег

fig, ax = plt.subplots()

x = cash_data.index
y1 = cash_data['third']
y2 = cash_data['second']
y3 = cash_data['third']

ax.bar(x, y1, label='third', color = 'red', alpha=0.3)
ax.bar(x, y2, label='second', color = 'yellow', alpha=0.8)
ax.bar(x, y3, label='third', color = 'green', alpha=0.9)

for i in range(len(y1)):
  plt.annotate(y1[i], (i-0.5, y1[i]))
  plt.annotate(y2[i], (i-0.5, y2[i]))
  plt.annotate(y3[i], (i-0.5, y3[i]))

fig.set_figwidth(15)    
fig.set_figheight(9)    
fig.set_facecolor('floralwhite')
ax.set_facecolor('seashell')
plt.xticks(rotation=50)
ax.set_xlabel('месяц', fontsize=20)
ax.set_ylabel('тыс. руб.', fontsize=20)
ax.set_title("Прогноз денежных остатков", fontsize=18)
ax.legend(fontsize=10)

plt.grid(linestyle='--', alpha=0.5)
plt.savefig('cash.jpg')
plt.show()

"""# Часть 3: Отправляем графики в notion

Как узнать нужный токен: https://www.notion.so/Find-Your-Notion-Token-5da17a8df27a4fb290e9e3b5d9ba89c4
"""

# Чиним баги неофициальной библиотеки notion на Python 
# Источник: https://github.com/jamalex/notion-py/blob/c9223c0539acf38fd4cec88a629cfe4552ee4bf8/notion/store.py#L280

from tzlocal import get_localzone

import notion
def call_load_page_chunk(self, page_id, limit): # Тут сама дописала limit в аргументы

    if self._client.in_transaction():
        self._pages_to_refresh.append(page_id)
        return

    data = {
        "pageId": page_id,
        "limit": 100,
        "cursor": {"stack": []},
        "chunkNumber": 0,
        "verticalColumns": False,
    }

    recordmap = self._client.post("loadPageChunk", data).json()["recordMap"]

    self.store_recordmap(recordmap)

def call_query_collection(
    self,
    collection_id,
    collection_view_id,
    search="",
    type="table",
    aggregate=[],
    aggregations=[],
    filter={},
    sort=[],
    calendar_by="",
    group_by="",
):

    assert not (
        aggregate and aggregations
    ), "Use only one of `aggregate` or `aggregations` (old vs new format)"

    # convert singletons into lists if needed
    if isinstance(aggregate, dict):
        aggregate = [aggregate]
    if isinstance(sort, dict):
        sort = [sort]

    data = {
        "collectionId": collection_id,
        "collectionViewId": collection_view_id,
        "loader": {
            "limit": 1000000,
            "loadContentCover": True,
            "searchQuery": search,
            "userLocale": "en",
            "userTimeZone": str(get_localzone()),
            "type": type,
        },
        "query": {
            "aggregate": aggregate,
            "aggregations": aggregations,
            "filter": filter,
            "sort": sort,
        },
    }

    response = self._client.post("queryCollection", data).json()

    self.store_recordmap(response["recordMap"])

    return response["result"]

def search_pages_with_parent(self, parent_id, search=""):
    data = {
        "query": search,
        "parentId": parent_id,
        "limit": 100,
        "spaceId": self.current_space.id,
    }
    response = self.post("searchPagesWithParent", data).json()
    self._store.store_recordmap(response["recordMap"])
    return response["results"]

notion.store.RecordStore.call_load_page_chunk = call_load_page_chunk
notion.store.RecordStore.call_query_collection = call_query_collection
notion.client.NotionClient.search_pages_with_parent = search_pages_with_parent

# Авторизация
client = NotionClient(token_v2=notion_token)

# Обращаемся к страничке
page = client.get_block(block_url)

# Чистим страницу от старых графиков
for i in page.children:
  i.remove()

# Список нарисованных графиков
plots = ['revenue.jpg', 'cash.jpg']

# И добавляем графики на страничку
for i in plots:
  photo = page.children.add_new(ImageBlock)
  time.sleep(600) #  Пауза на 10 минут, чтобы notion не забанил
  photo.upload_file(i)
  time.sleep(600) #  Еще пауза на 10 минут