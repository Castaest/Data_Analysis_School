#!/usr/bin/env python
# coding: utf-8

# In[1]:


import yfinance as yf
import pandas as pd


# In[2]:


crude_oil_ticker = "CL=F"
crude_oil = yf.Ticker(crude_oil_ticker)
hist = crude_oil.history()


# In[3]:


data = yf.download(crude_oil_ticker, start = '2021-01-01')


# In[4]:


euro = yf.download('EURUSD=X', start = '2021-01-01')


# In[5]:


rur = yf.download('USDRUB=X', start = '2021-01-01')


# In[6]:


# Затраты на производство
PRODUCTION_COST = 400 # (EUR)

# Расходы на логистику
EU_LOGISTIC_COST_EUR = 30 # в Европу в евро
CN_LOGISTIC_COST_USD = 130 # в Китай в долларах

# * Справочная информация по клиентам(объемы, локации, комментарии) 
customers = {
    'Сonty':{
        'location':'EU',
        'volumes':200,
        'comment':'moving_average'
    },
    
    'Triangle':{
        'location':'CN',
        'volumes': 30,
        'comment': 'monthly'
    },
    'Stone':{
        'location':'EU',
        'volumes': 150,
        'comment': 'moving_average'
    },
    'Ant':{
        'location':'EU',
        'volumes': 70,
        'comment': 'monthly'
    }
}
# Скидки
discounts = {'99': 0.01, # до 100 тонн 1%
             '299': 0.05, #  до 300 тонн 5%
             '300': 0.1}   # больше 300 тонн 10%


# In[7]:


# функция расчета скидки по словарю скидок
def get_discount(amount):
    '''
    функция возвращает размер скидки по переданному значению объема закупки
    функция использует глобальный словарь discounts
    если на вход дано отрицательное значение, функция возвращает нулевую скидку
    ВАЖНО: словарь скидок должен быть упорядочен по возрастанию объемов закупок
    '''
    if amount < 0:
        return 0
    for k, v in discounts.items():
        if amount <= int(k):
            return v
    return v   


# In[8]:


# Базовая формула цены на заводе
# Сделаем датафрейм с ценами (нефть, курс евро к доллару, курс рубля к доллару)
df = pd.concat([data.resample('M').mean()['Close'], euro.resample('M').mean()['Close'], rur.resample('M').mean()['Close']], axis = 1)
df.columns = ['Oil', 'Eurusd', 'Usdrur']

# добавим цену производства тонны СК 
# базовая цена - в евро
df['Basis'] = round(df['Oil'] * 10 / df['Eurusd'] + PRODUCTION_COST, 2)


# In[11]:


# добавим в датафрейм расчет цены для каждого клиента
# для клиентов Европы цены в евро, для клиентов Китая цены в долларах

for i in customers.keys():
    if customers[i]['location'] == 'EU':
        df[i] = customers[i]['volumes'] * EU_LOGISTIC_COST_EUR * df['Basis'] * get_discount(customers[i]['volumes'])
    elif customers[i]['location'] == 'CN':
        df[i] = customers[i]['volumes'] * CN_LOGISTIC_COST_USD * df['Basis'] * df['Eurusd'] * get_discount(customers[i]['volumes'])
    else:
        print(f' Внимание: неизвестная локация!')
    df[i] = df[i].astype(int)    
        


# In[24]:


# записываем расчетные цены в один файл и для каждого клиента - в отдельный файл
import os
clients_path = 'for_clients'
os.makedirs(clients_path, exist_ok = True)
import matplotlib.pyplot as plt

xlfilepath = 'offer_prices.xlsx'
with pd.ExcelWriter(xlfilepath, engine = 'xlsxwriter') as writer:
    for client_name, client_info in customers.items():
        client_df = df[['Basis', client_name]].copy()

        if client_info.get('location') == 'EU':
            client_df['logistics per tonne'] = EU_LOGISTIC_COST_EUR
        elif client_info.get('location') == 'CN':
            client_df['logistics per tonne'] = CN_LOGISTIC_COST_USD
    
        if client_info.get('volumes'):
            client_df['volumes'] = client_info.get('volumes')

        client_df['discount'] = client_df['volumes'].apply(get_discount)
        client_df.rename(columns = {client_name: 'Total price'}, inplace = True)
        
        client_df['Total price'].plot(color = 'red', linestyle = 'dashed')
        plt.title(f'Client {client_name} total price')
        if client_info.get('location') == 'EU':
            plt.ylabel('EUR')
        else:
            plt.ylabel('USD')
        plt.tight_layout()
        plt.savefig(f'{client_name}_ck_price.png')
        plt.close()

        client_df = client_df.round(2)
        client_df = client_df.reset_index()
        client_df.Date = client_df.Date.dt.strftime('%B %Y')

        max_row, max_col = client_df.shape
        client_df.to_excel(writer, sheet_name = client_name, startrow = 1, header = False, index = False)
        workbook = writer.book
        worksheet = writer.sheets[client_name]
        column_settings = [{'header': column} for column in client_df.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
        worksheet.insert_image(max_row + 3, 1, f'{client_name}_ck_price.png')
        
        # запись отдельного файла для каждого клиента

        file_to_open = os.path.join(clients_path, client_name + '.xlsx')
        with pd.ExcelWriter(file_to_open, engine = 'xlsxwriter') as writer_one:
            client_df.to_excel(writer_one, sheet_name = client_name, startrow = 1, header = False, index = False)
            workbook = writer_one.book
            worksheet = writer_one.sheets[client_name]
            column_settings = [{'header': column} for column in client_df.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
            worksheet.insert_image(max_row + 3, 1, f'{client_name}_ck_price.png')
            

