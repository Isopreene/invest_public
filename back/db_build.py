import os
import json
from back.trade import Trading

class DBBuilder:
    def create_and_update_db(self, trade_client:Trading, shares_to_add):
        stocks = self.convert_all_stocks(trade_client.get_all_stocks())
        if os.path.exists('back/stocks_db.json'):
            path = 'back/stocks_db.json'
        elif os.path.exists('stocks_db.json'):
            path = 'stocks_db.json'
        else:
            path = f'{os.getcwd()}/stocks_db.json'
        with open(path, 'wt', encoding='UTF-8') as file:
            json.dump({'stocks': list(stocks) + shares_to_add},
                      sort_keys=False,
                      indent=4,
                      separators=(',', ': '),
                      ensure_ascii=False,
                      fp=file)
            return file


    @staticmethod
    def convert_all_stocks(stocks):
        conv = map(lambda x: {'ticker': x.ticker, 'name': x.name.lower(), 'figi': x.figi, 'lot': x.lot},
                   filter(lambda x: x.currency == 'rub', stocks.instruments))
        return conv
