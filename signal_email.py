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
import numpy as np
from datetime import datetime, timedelta

#DATA GATHERING

start_date = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
def gatherdata(ticker, periodicity):
  data = yf.download(
      tickers = ticker,
      start=start_date,
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

def create_signal_df(df, ticker):
  df_transposed = df[["buy_trend"]].tail(7).T
  df_transposed = df_transposed.rename(index={'buy_trend': ticker})
  return df_transposed


#MAIN

rule1_tickers = ["AEM", "AGI", "ANET", "ASML", "AU", "AVGO", 
                 "DXCM", "EME", "FIX", "FN", "FNV", "FTNT", "GCT", "GFI", "GMED", 
                 "GOOG", "GRMN", "INTU", "ISRG", "MEDP", "META", "MPWR", "MSFT", 
                 "NFLX", "NVDA", "OR", "PAYC", "RMD", "ROL", "SCCO", "TSM", "TW", 
                 "UI", "V", "VEEV", "WPM"
                 ]

index_tickers = ["QQQ", "VOO"]

crypto_alts = ["BTC-USD", "SOL-USD", "SUI20947-USD", "SLV", "PAXG-USD", 
               "URA", "COPX", "PPLT", "PALL", "LIT"]

other_tickers = [
    "005930.KS", 
    "AAPL", "ABBV", "ADBE", "ADSK",  "AMAT", "AMD", "AMZN", "APH", "ARM",  "AXP", 
    "B", "BAP", "BAM", "BKNG", "BRK-B", "BSY", "BWXT", 
    "CAAP", "CART",  "COST", "CW", "CGNX",
    "EBAY", 
    "FICO","FISV", "FVRR", 
    "GLW", 
    "HD", "HEI", "HWM", 
    "IBKR", "INCY", "INTC",  
    "JNJ", 
    "KO", 
    "LITE", "LLY", "LRCX", "LULU", 
    "MA", "MCD", "MCK", "MDLZ", "MELI",   "MSCI", 
    "NBIX",  "NOW", 
    "OLLI", "ONON",  
    "PEP", "PG", "PLTR",  "PYPL", 
    "QBTS", "QCOM", 
    "RGTI",   "ROK",
    "SAP",  "SNDK", 
    "TCEHY", "TGT", "TMUS", "TSLA",  
    "UBER",   
    "VIK",  "VZ", 
    "WMT", "WWD",  
    "ZTS"       
]

periodicity = "1d"

def create_df(tickers):
  big_df = pd.DataFrame()
  for ticker in tickers:
    ticker_df = gatherdata(ticker, periodicity)
    df_result = calculate_buy_line(ticker_df)
    signal_df = create_signal_df(df_result, ticker)
    big_df = pd.concat([signal_df, big_df], axis=0)
    big_df = big_df.iloc[:, 2:]
    unique_counts = big_df.apply(lambda x: x.dropna().nunique(), axis=1)
    big_df = big_df.loc[unique_counts.sort_values(ascending=False).index]
    emoji_map = {-1.0: '🔴', 0.0: '⚪', 1.0: '🟢'}
    big_df_emojified = big_df.replace(emoji_map).fillna('-')
    
  return big_df_emojified

index_df = create_df(index_tickers)
rule1_df = create_df(rule1_tickers)
other_df = create_df(other_tickers)
crypto_df = create_df(crypto_alts)
  


def send_email():
    # Fetch credentials from environment variables  
    EMAIL_ADDRESS = os.environ.get('EMAIL_USER')    
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    RECIPIENT = os.environ.get('EMAIL_RECEIVER')

    msg = EmailMessage()
    msg['Subject'] = 'Daily Signals setting positions'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT
    msg.set_content(f"Index:  {index_df.to_string()} \n\n Rule 1: {rule1_df.to_string()} \n\n Other Stocks: {other_df.to_string()} \n\n Crypto: {crypto_df.to_string()}")


    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully.")

if __name__ == "__main__":
    send_email()
