import pandas
import locale
import requests_cache
from pandas_datareader import data as pd
import datetime as dt
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

init_notebook_mode(connected=True)

pandas.set_option('display.max_rows', 1000)
pandas.set_option('display.max_columns', 100)
pandas.set_option('display.width', 1000)

locale.setlocale(locale.LC_ALL, 'en_US')
expire_after = dt.timedelta()
session = requests_cache.CachedSession(cache_name='cache', backend='sqlite', 
                                       expire_after=expire_after)

def dividend(ticker):
    return pd.DataReader(ticker, 'yahoo-actions')

def mutual_fund_fee(ticker):
    pass

def ytd_supports(prices):
    max = 0
    support = None
    if len(prices) < 3:
        return support

    for i in range(1, len(prices)-1):
        if prices[i-1] > prices[i] and prices[i] < prices[i+1]:
            length = 0
            for j in reversed(range(i)):
                if prices[j-1] > prices[j]:
                    length += 1
                else: 
                    break
            for j in range(i, len(prices)-1):
                if (prices[j] < prices[j+1]):
                    length += 1
                else: 
                    break
            if length > max:
                max = length
                support = prices[i]
    return support

def ytd_resistances():
    pass

def ytd_corrections():
    pass

def ytd(tickers):
    now = dt.datetime.now()
    
    # map of ytd firstday price, today price, performance, high & low
    ytd_perf = {} 
    
    for ticker in tickers:
        ytd = pd.get_data_yahoo(ticker, start=dt.datetime(now.year, 1, 1),
                                 end=None, session=session)
        
        # ytd performance
        perf = (ytd['Close'][-1] - ytd['Close'][0]) / ytd['Close'][0]
        
        # firstday price, today price & performance 
        ytd_perf[ticker] = [ytd['Close'][0], ytd['Close'][-1], perf]
        
        # sort dataframe in ascending order
        ytd.sort_values(by=['Close'], inplace=True)
        
        high = (ytd['Close'][-1], pandas.to_datetime(ytd.index.values[-1]).date())
        low = (ytd['Close'][0], pandas.to_datetime(ytd.index.values[0]).date())
        ytd_perf[ticker].extend([high, low])       
    return ytd_perf

def get_quotes():
    pass

def perf(tickers):
    quotes = pd.get_quote_yahoo(tickers, session=session)
    return quotes['ytdReturn']

    '''
    for ticker in tickers:
        quote = pd.get_quote_yahoo(ticker, start=start, end=end, session=session)
        print(quote['ytdReturn'])
    '''

def analyze(portfolio, ytd):
    for index, row in portfolio.iterrows():
        if 'Buy($)' not in row:
            continue
        portfolio.at[index, 'Cost'] = round(row['Buy($)'] * row['Share'], 2)
        if row['Symbol'] != 'CASH':
            if pandas.isna(row['Sell($)']):
                portfolio.at[index, 'Gain($)'] = round((ytd[row['Symbol']][1] - 
                             row['Buy($)']) * row['Share'], 2)
                portfolio.at[index, 'Value'] = round(ytd[row['Symbol']][1] * 
                            row['Share'], 2)
                portfolio.at[index, 'YTD($)'] = round((ytd[row['Symbol']][1] - 
                             ytd[row['Symbol']][0]) * row['Share'], 2)
            else:
                portfolio.at[index, 'Gain($)'] = round((row['Sell($)'] - 
                            row['Buy($)']) * row['Share'], 2)
                portfolio.at[index, 'Value'] = 0
                portfolio.at[index, 'YTD($)'] = 0    
                portfolio.at[index, 'YTD($)'] = 0
        else:
            portfolio.at[index, 'Gain($)'] = 0
            portfolio.at[index, 'Value'] = row['Share']
    return portfolio

def summarize(summary, ytd):
    for index, row in summary.iterrows():
        if index != 'CASH':
            summary.at[index, 'YTD(%)'] = round(ytd[index][2]*100, 2)
            summary.at[index, 'ytd High'] = round(ytd[index][3][0], 2)
            summary.at[index, 'ytd High Date'] = ytd[index][3][1]
            summary.at[index, 'ytd Low'] = round(ytd[index][4][0], 2)
            summary.at[index, 'ytd Low Date'] = ytd[index][4][1]
    if 'Buy($)' in summary:
        total = summary['Value'].sum() 
        summary['Allocation(%)'] = summary['Value'] / total * 100
        summary['Gain(%)'] = round(100*summary['Gain($)']/summary['Cost'], 2)
    return summary

def graph(summary, metric):
    if metric == 'YTD':
        graph = go.Bar(x=summary['Symbol'], y=summary[metric], name=metric)
    elif metric == 'Allocation(%)':
        s = summary[summary[metric] != 0]
        graph = go.Pie(labels=s['Symbol'], values=s[metric])
        
    figure = go.Figure(graph)
    figure.update_layout(title_text='Payflex YTD performance')
    figure.show()
    #iplot(figure)
       
def display(summary):
    if 'Buy($)' in summary:
        total = summary['Value'].sum()  
        print('Net: ', locale.format_string('%d', total, grouping=True))
        print('ytd: ', locale.format_string('%d', 
                                            round(summary['YTD($)'].sum(), 2), 
                                            grouping=True))
        print('Since inception: ', 
              locale.format_string('%d', 
                                   round(summary['Gain($)'].sum(), 2), 
                                   grouping=True))
    
if __name__ == '__main__':
    portfolio = pandas.read_excel('Research.xlsx').drop_duplicates()
    #portfolio.drop_duplicates(inplace=True)
    
    # YTD
    #perf = perf(portfolio['Symbol'])
    portfolio['YTD'] = perf(portfolio['Symbol']).values
    print(portfolio)
    
    '''
    # ytd performance
    ytd = ytd(portfolio['Symbol'].unique())
    '''
    
    # Analyze
    '''
    portfolio = analyze(portfolio, ytd)
    
    summary = summarize(portfolio.groupby('Symbol').sum(), ytd)
    summary.reset_index(inplace=True)
    summary.sort_values(by=['YTD'], inplace=True)
    graph(summary, 'YTD')
    
    if 'Allocation(%)' in summary:
        summary.sort_values(by=['Allocation(%)'], inplace=True)
        graph(summary, 'Allocation(%)')
        display(summary)
    
    #print(dividend('POGRX'))
    '''