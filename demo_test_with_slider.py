import streamlit as st
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import numpy as np

df = pd.read_csv('C:\\Users\\aab\\Documents\\Обучение\\housing.csv')

if st.button('Отобразить первые пять строк'):
    st.write(df.head())

train_size = st.slider('Выбрать размер обучающей выборки, % объема данных:', 5, 95, 80)

if st.button('Обучить модель'):
    X_train, X_test, y_train, y_test = train_test_split(df.drop('MEDV', axis=1),
                                                        df['MEDV'],
                                                        test_size = (100 - train_size) / 100,
                                                        random_state = 2100)
    st.write('Разделили данные и передали в обучение')
    regr_model = XGBRegressor()
    regr_model.fit(X_train, y_train)
    pred = regr_model.predict(X_test)
    st.write('Обучили модель, MAE = ' + str(mean_absolute_error(y_test, pred)))
