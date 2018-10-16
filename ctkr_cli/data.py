#!/usr/bin/env python3

import async
import pickle
import ccxt
from models import (
    Exchange, 
    Marketplace, 
    Ticker
)

class MarketData(object):
    def __init__(self, file_path='data/market_data.p', refresh=False):
        if refresh:
            self.market_data = self.refresh_data(file_path)
        else:
            try:
                self.market_data = self.load_data(file_path)
            except FileNotFoundError:
                self.market_data = self.refresh_data(file_path)

    def get_market(self, exch):
        try:
            mkt = Marketplace(exch)
            data = {
                'countries': mkt.countries,
                'coins': mkt.coins,
                'symbols': mkt.symbols,
                'error': 'N/A'
            }

        except Exception as e:
            data = {
                'countries': 'N/A',
                'coins': 'N/A',
                'symbols': 'N/A',
                'error': e.__class__.__name__
            }

        return [exch, data]

    def request_markets(self, n_workers=40):
        return async.run_loop(
            self.get_market, 
            n_workers, 
            ccxt.exchanges
        )

    def save_data(self, file_path):
        with open(file_path, 'wb') as fp:
            pickle.dump(
                self.market_data, 
                fp, 
                protocol=pickle.HIGHEST_PROTOCOL
            )
   
    def load_data(self, file_path):
        with open(file_path, 'rb') as fp:
            self.market_data = pickle.load(fp)
        return self.market_data

    def refresh_data(self, file_path):
        self.market_data = self.request_markets()
        self.save_data(file_path)


class TickerData(MarketData):
    def __init__(self):
        MarketData.__init__(self) #self.market_data

    def __call__(self, symbol, country=None, data='last_price', n_workers=40):
        return self.request_tickers(symbol, country, data, n_workers)

    def get_ticker(self, exch, symbol, data):
        result = 'N/A'
        
        try:
            ticker = Ticker(exch, symbol)
        except Exception as e:
            result = e.__class__.__name__
        else:
            if getattr(ticker, data):
                result = getattr(ticker, data)
        
        return [exch, result]

    def request_tickers(self, symbol, country, data, n_workers):        
        return async.run_loop(
            self.get_ticker, 
            n_workers, 
            self.filter_markets(symbol, country), 
            symbol,
            data 
        )

    def filter_markets(self, symbol, country):
        if country:
            markets = {
                k: v for k, v in self.market_data.items() 
                if symbol in v['symbols'] 
                and country in v['countries']
            }

        else:
            markets = {
                k: v for k, v in self.market_data.items() 
                if symbol in v['symbols']
            }

        return markets
