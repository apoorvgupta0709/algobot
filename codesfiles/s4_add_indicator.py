from datetime import datetime, timedelta
from tkinter.tix import COLUMN
import pandas as pd
import pandas_ta as pta
import ta
import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots



class bnf_data:
    
    today_date = datetime.today().strftime('%Y-%m-%d')
    df_bnfclass = pd.DataFrame()
    
    
    def __init__(self, e = 50, r = 20, bbl = 20, bbs = 1.0, eb = 5, lr = 50, sr = 50, a = 7,sl_ratio = 1.2, rr = 2, filepath = f'./Daytrading/file for trading bot.csv'):
        
        self.e = e
        self.r = r
        self.bbl = bbl
        self.bbs = bbs #write in format of x.0 or 0.x

        #Variables for function calculating uptrend/downtrend based on ema20
        self.eb = eb

        #Variables for filtering rsi
        self.lr = lr
        self.sr = sr

        #Variables for ATR, RR
        self.a = a
        self.sl_ratio = sl_ratio
        self.rr = rr

        self.df = pd.read_csv(filepath)
        #self.df.loc[:,'Date'] = pd.to_datetime(self.df['Date_w'] + ' ' + self.df['Time'], format='%d-%m-%Y %H:%M')
        self.df['Date'] = pd.to_datetime(self.df['Date_w'] + ' ' + self.df['Time'], format='%d-%m-%Y %H:%M')
        self.df = self.df.sort_values(by='Date', ascending=True)
        self.df.drop(['Time', 'Date_w', 'volume'], axis = 1, inplace = True)
        # self.df["Date"] = self.df["Date"].astype(str).apply(lambda x: x[:-9])
        # self.df.drop(columns = ['Unnamed: 0', 'Time', 'Date_w'], axis = 0, inplace = True)
        # self.df['Date']=pd.to_datetime(self.df['Date'],format='%Y.%m.%d %H:%M')
        self.df.set_index("Date", inplace=True)
        self.df = self.df[self.df.high!=self.df.low]
        self.df.astype({'open' : 'int', 'high' : 'int', 'low' : 'int', 'close' : 'int'})
        #print("This has run")
        
    def priceFetcher(self):
        
        self.df_bnfclass = self.df

    def priceFetcher_test(self):
        
        self.df = pd.read_csv(f'./Backtesting/file for sample testing bot.csv')
        self.df.loc[:,'Date'] = pd.to_datetime(self.df['datetime'], format='%Y-%m-%d %H:%M')
        self.df.set_index("Date", inplace=True)
        self.df_bnfclass = self.df
        
    def add_indicators(self):
        self.df_bnfclass['ema20'] = ta.trend.EMAIndicator(self.df_bnfclass.close, window = self.e, fillna = True).ema_indicator().astype(int)
        self.df_bnfclass['RSI'] = ta.momentum.RSIIndicator(self.df_bnfclass.close, window = self.r).rsi().fillna(0).astype(int)
        self.df_bnfclass['bbh'] = ta.volatility.BollingerBands(self.df_bnfclass.close, window = self.bbl, window_dev = self.bbs).bollinger_hband().fillna(0).astype(int)
        self.df_bnfclass['bbl'] = ta.volatility.BollingerBands(self.df_bnfclass.close, window = self.bbl, window_dev = self.bbs).bollinger_lband().fillna(0).astype(int)
        self.df_bnfclass['atr'] = ta.volatility.average_true_range(self.df_bnfclass.high, self.df_bnfclass.low, self.df_bnfclass.close, window = self.a, fillna = False).astype(int)
        self.df_bnfclass = self.df_bnfclass.iloc[max(self.e, self.r, self.bbl):]

    def ema_trend(self):

        # Calculate signals using vectorized operations
        self.df_bnfclass.loc[:, 'upt'] = (self.df_bnfclass['close'] >= self.df_bnfclass['ema20']).rolling(window = self.eb).min().fillna(False).astype(bool)
        self.df_bnfclass.loc[:, 'dnt'] = (self.df_bnfclass['close'] <= self.df_bnfclass['ema20']).rolling(window = self.eb).min().fillna(False).astype(bool)

        # Assign signals based on conditions
        self.df_bnfclass['ema20signal'] = np.select(
            [(self.df_bnfclass['upt'] & self.df_bnfclass['dnt']), self.df_bnfclass['upt'], self.df_bnfclass['dnt']],
            [3, 2, 1],
            default=0
        )

        # Drop temporary columns
        self.df_bnfclass.drop(columns=['upt', 'dnt'], inplace=True)
        
    def trade_signal(self):
        
        # Vectorized conditions
        condition1 = (self.df_bnfclass['ema20signal'] == 2) & (self.df_bnfclass['close'] <= self.df_bnfclass['bbl']) & (self.df_bnfclass['RSI'] < self.lr)
        condition2 = (self.df_bnfclass['ema20signal'] == 1) & (self.df_bnfclass['close'] >= self.df_bnfclass['bbh']) & (self.df_bnfclass['RSI'] > self.sr)

        # Initialize TotalSignal column to 0
        self.df_bnfclass['TotalSignal'] = 0

        # Apply conditions
        self.df_bnfclass.loc[condition1, 'TotalSignal'] = 2
        self.df_bnfclass.loc[condition2, 'TotalSignal'] = 1

        #shifting by 1 to compare
        mask = self.df_bnfclass['TotalSignal'].eq(self.df_bnfclass['TotalSignal'].shift(1))

        # Step 2: Where the mask is True (the value is the same as the previous one), replace with NaN
        self.df_bnfclass['TotalSignal1'] = self.df_bnfclass['TotalSignal'].mask(mask)
        
        #df['TotalSignal1'] = df['TotalSignal'].mask(df['TotalSignal'].duplicated(keep='first'))
        self.df_bnfclass['TotalSignal1'].fillna(0, inplace = True)
        self.df_bnfclass['TotalSignal1'] = self.df_bnfclass['TotalSignal1'].astype(int)

        # Return the modified DataFrame
        return self.df_bnfclass
        
    def pointposbreak(self, x):
        if x['TotalSignal']==1:
            return x['high']+1e-4
        elif x['TotalSignal']==2:
            return x['low']-1e-4
        else:
            return np.nan
    
    def full_loop(self):
        #slice dataset for faster computation
        #self.df_bnfclassf1 = self.df_bnfclass.tail(2500).copy()
        self.priceFetcher()
        self.add_indicators()
        self.ema_trend()
        self.trade_signal()
        self.df_bnfclass['pointposbreak'] = self.df_bnfclass.apply(lambda row: self.pointposbreak(row), axis=1)
        self.df_bnfclass.to_csv(f'file for check dataframe order{datetime.now().date()}.csv')
        
    def full_loop_test(self):
        #slice dataset for faster computation
        #self.df_bnfclassf1 = self.df_bnfclass.tail(2500).copy()
        self.priceFetcher_test()
        self.add_indicators()
        self.ema_trend()
        self.trade_signal()
        self.df_bnfclass['pointposbreak'] = self.df_bnfclass.apply(lambda row: self.pointposbreak(row), axis=1)
        self.df_bnfclass.to_csv(f'file for check dataframe order{datetime.now().date()}.csv')

    
    def plot_window(self, st = 0):
        dfpl = self.df_bnfclass[st:st+430]
        dfpl.reset_index(inplace=True)
        fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                        open=dfpl['open'],
                        high=dfpl['high'],
                        low=dfpl['low'],
                        close=dfpl['close']),
                        go.Scatter(x=dfpl.index, y=dfpl.ema20, 
                                   line=dict(color='blue', width=1), 
                                   name="ema20"), 
                        go.Scatter(x=dfpl.index, y=dfpl[self.bbl], 
                                   line=dict(color='green', width=1), 
                                   name="BBL"),
                        go.Scatter(x=dfpl.index, y=dfpl[self.bbu], 
                                   line=dict(color='green', width=1), 
                                   name="BBU")])

        fig.add_scatter(x=dfpl.index, y=dfpl['pointposbreak'], mode="markers",
                        marker=dict(size=10, color="MediumPurple"),
                        name="Signal")
        fig.show()    