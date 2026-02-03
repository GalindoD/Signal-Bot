import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv, find_dotenv
import subprocess
import sys


# This finds the .env file and loads the variables
load_dotenv(find_dotenv())


def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_package("yfinance")   
install_package("TA-Lib")



#IMPORT LIBS

import subprocess
import sys
import pandas as pd
import yfinance as yf
import talib

#DATA GATHERING

def gatherdata(ticker, periodicity):
  data = yf.download(
      tickers = ticker,
      #start="2025-01-01",
      #end="2026-01-20",
      period="max",
      interval=periodicity,
      ignore_tz=True,
      auto_adjust=True)
  data_df = data.copy()
  data_df.columns = ["close", "high", "low", "open", "volume"]
  return data_df


# Calculate the bear, bull and neutral signal

def calculate_buy_line(df, fast_len=30, slow_len=60, atr_len=60, atr_mult=0.18):
    # 1. Calculate Moving Averages
    # Pine: emaFast = ema(close, emaFastLen)
    df['ema_fast'] = talib.EMA(df['close'], timeperiod=fast_len)

    # Pine: emaSlow = ema(close, emaSlowLen)
    df['ema_slow'] = talib.EMA(df['close'], timeperiod=slow_len)

    # Pine: emaDiff = emaFast - emaSlow
    df['ema_diff'] = df['ema_fast'] - df['ema_slow']

    # 2. Calculate ATR (Average True Range)
    # Pine: atr(emaMarginATRLen)
    # Note: talib.ATR requires High, Low, and Close
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=atr_len)

    # 3. Case Differentiation (Logic)
    # Define the margin threshold
    threshold = atr_mult * df['atr']

    # Pine: emaBull = emaDiff > emaMarginATRMult * atr
    condition_bull = df['ema_diff'] > threshold

    # Pine: emaBear = emaDiff < -emaMarginATRMult * atr
    condition_bear = df['ema_diff'] < -threshold

    # Create a 'trend' column to represent the state
    # 1 = Bull, -1 = Bear, 0 = Neutral
    df['buy_trend'] = 0
    df.loc[condition_bull, 'buy_trend'] = 1
    df.loc[condition_bear, 'buy_trend'] = -1


    # Define Position:
    # We map the trend, -1 to 0, so that it only entres on the upside and flat at downside
    df['position'] = df['buy_trend'].replace(-1, 0)

    return df


# Create Signal DF

def create_signal_df(df):
  df_transposed = df[["buy_trend"]].tail(6).T
  df_transposed = df_transposed.rename(index={'buy_trend': ticker})
  return df_transposed


#MAIN

ticker_list = ["BTC-USD", "PAXG-USD", "SOL-USD", "SUI20947-USD", "USDMXN=X", "QQQ"]
periodicity = "1d"

big_df = pd.DataFrame() # Initialize big_df as an empty DataFrame

for ticker in ticker_list:
  ticker_df = gatherdata(ticker, periodicity)
  df_result = calculate_buy_line(ticker_df)
  signal_df = create_signal_df(df_result)
  big_df = pd.concat([signal_df, big_df], axis=0)

#print(big_df)





def send_email():
    # Fetch credentials from environment variables  
    EMAIL_ADDRESS = os.environ.get('EMAIL_USER')    
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    RECIPIENT = os.environ.get('EMAIL_RECEIVER')

    msg = EmailMessage()
    msg['Subject'] = 'Daily Signals settig positions'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT
    msg.set_content('Here should be the table with the signals. \n\n' + big_df.to_string())

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully.")

if __name__ == "__main__":
    send_email()


#print(EMAIL_ADDRESS)
