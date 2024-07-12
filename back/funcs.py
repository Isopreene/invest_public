from time import sleep
import re
from tqdm import tqdm
import json
import os
from back.telegram import TelegramParsing
from back.gpt import GPT
from back.trade import Trading
import traceback
from decimal import Decimal
from tinkoff.invest.exceptions import RequestError
from tinkoff.invest.utils import money_to_decimal


class Functions:

    def show_balance(self, trade_client):
        return trade_client.show_balance()


    def close_all_positions(self, trade_client:Trading):
        trade_client.cancel_limit_orders()
        portfolio = trade_client.show_portfolio()
        for position in portfolio:
            figi = position.figi
            lot = self.convert_parameters(data=self.get_stocks_db_data(),search='lot', company_figi=figi)
            while True:
                sleep(0.3)
                if position.balance > 0:
                    trade_client.sell_by_figi(figi, position.balance//lot)
                else:
                    trade_client.buy_by_figi(figi=figi, lot=lot, money=1, quantity=position.balance//lot)
                new_portfolio = trade_client.show_portfolio()
                if position.figi not in new_portfolio:
                    print(f'позиция {position.figi} закрыта')
                    break

    @staticmethod
    def convert_parameters(data, search='figi',
                           company_name=None, company_ticker=None,
                           company_figi=None):
        for company in data['stocks']:
            if company['name'] == company_name or company['ticker'] == company_ticker or \
                    company['figi'] == company_figi:
                return company[search]

    def get_stock_parameters(self, post_for_trading: str, data, gpt_client: GPT):
        figi = ''
        post = post_for_trading.replace('\\n', '')
        if 'тикер' in post:  # если есть тикер в тексте поста
            ticker = re.search('тикер:?\s*([a-zA-Z]{1,6})', post)
            if ticker:
                ticker = ticker.group(1).upper()
                print(f'по паттерну {ticker}')
            figi = self.convert_parameters(data=data, company_ticker=ticker)
            print(f'сконвертировал {figi}')
            # if 'тикер' not in post or not figi:  # если нет тикера
        #     figi = gpt_client.check(post)
        #     if figi:
        #         print(f'GPT нашёл:{figi}')
        #     else:
        #         print(f'GPT не нашёл')
        else:
            print('нет тикера, включите гпт :(')
        return figi

    @staticmethod
    def get_path():
        if os.path.exists('back/stocks_db.json'):
            path = 'back/stocks_db.json'
        elif os.path.exists('stocks_db.json'):
            path = 'stocks_db.json'
        else:
            path = f'{os.getcwd()}/back/stocks_db.json'
        return path

    def get_stocks_db_data(self):
        sleep(0.1)
        with open(self.get_path(), 'rt', encoding='UTF-8') as file:
            sleep(0.1)
            data = json.load(file)
        sleep(0.1)
        return data

    def parse(self, tg_client:TelegramParsing, gpt_client:GPT, trade_client:Trading):
        post = tg_client.get_post_for_trading(trade_client)  # получаем список новых, ещё не обработанных постов
        if not post:
            return []
        data = self.get_stocks_db_data()
        figi = self.get_stock_parameters(post, data, gpt_client)  # получаем figi для покупки
        lot_ = self.convert_parameters(data=data, company_figi=figi, search='lot')
        return [figi, lot_]

    @staticmethod
    def send_read_acknowledge(client_tg:TelegramParsing, private_channel_id):
        with client_tg.client as client:
            client.send_read_acknowledge(private_channel_id)
        return True

    @staticmethod
    def trailing_or_regular(trade_client, figi, average_price, amount_of_shares):
        print(f'спим стартовое время {trade_client.start_time} сек')
        for _ in range(trade_client.start_time):
            try:
                sleep(1)
                market_price = trade_client.get_last_price(figi, dec=True)
                if market_price >= average_price * Decimal(str(1.01)):
                    response = trade_client.create_trailing_stop(figi=figi, quantity=amount_of_shares,
                                                                 last_price=market_price)
                    if response:
                        print('выставлен трейлинг-стоп')
                        return True
            except RequestError:
                sleep(3)
            except Exception as e:
                print(e, f'{traceback.format_exc()}\n')
                sleep(5)
        print('Трейлинга нет, ставим обычные стоп-ордера')
        return
    def buy(self, trade_client, figi, lot):
        leverage = 1 if not trade_client.use_lev else trade_client.get_leverage_by_figi(figi)
        leverage = 5 if leverage > 5 else leverage
        try:
            response = trade_client.buy_by_figi(figi=figi, lot=lot, money=trade_client.money * leverage)
            amount_of_shares = response.lots_executed
            average_price = money_to_decimal(response.executed_order_price)
            print(f'купили {figi}\n{trade_client.show_portfolio_user()}')
        except (RequestError, AttributeError):
            print(f'на счёте было {figi}\n{trade_client.show_portfolio_user()}')
            sleep(0.1)
            hist = next(trade_client.get_history(figi))
            average_price:float|Decimal = Decimal(str(round(hist['payment']/hist['quantity'], 10)))
            portfolio = trade_client.show_portfolio()
            for x in portfolio:
                if x.figi == figi:
                    amount_of_shares = x.balance//lot
                    break
            else:
                amount_of_shares = 0
        except StopIteration:
            return 0, 0
        return amount_of_shares, average_price

    def get_quantity(self, amount_of_shares, trade_client):
        quantity = int(amount_of_shares / trade_client.sells)
        last_quantity = amount_of_shares - quantity * (trade_client.sells - 1)
        percentage = Decimal(str(round((trade_client.finish_percent - trade_client.start_percent) /
                                       (trade_client.sells - 1), 2)))
        return quantity, last_quantity, percentage

    def sell(self, trade_client, figi, orders_id, lot):
        sleep(1)
        pbar = tqdm(desc='while', total=trade_client.sells)
        while True:
            try:
                print(f'осталось ждать {trade_client.sleeping_time} сек')
                posted_orders = trade_client.get_stop_orders(figi)
                posted_orders = sorted(posted_orders, key=lambda x: orders_id[x][0])
                sleep(0.3)
                if not posted_orders:
                    print('Заявок больше нет')
                    return
                sleep(trade_client.sleeping_time)
                # если i-ая заявка НЕ отработалась и висит, то снимаем последнюю
                order_to_cancel = posted_orders[-1] if posted_orders else False
                sleep(0.3)
                resp = trade_client.cancel_stop_order(order_id=order_to_cancel)
                if resp:
                    print(
                        f'Заявка {orders_id[order_to_cancel][0] + 1} ({orders_id[order_to_cancel][2]}%) на продажу '
                        f'снята, осталось {len(posted_orders) - 1 if posted_orders else 0}')
                else:
                    print('Error 1')
                response = trade_client.sell_by_figi(figi, quantity=orders_id[order_to_cancel][1])
                if response:
                    print(f'Продали {figi} {orders_id[order_to_cancel][1] * lot} шт')
                pbar.update(1)
            except Exception as e:
                print(e)
                sleep(3)

    def buy_and_sell(self, figi_and_lot:list, trade_client:Trading,manual:bool):
        # self.close_all_positions(trade_client)
        figi, lot = figi_and_lot[0], figi_and_lot[1]
        amount_of_shares, average_price = self.buy(trade_client, figi, lot)
        if not amount_of_shares:
            print('не хватило денег')
            return
        if manual:
            print('торговля в ручном режиме')
            while True:
                try:
                    holdings = trade_client.show_portfolio()
                    if not holdings:
                        return
                    else:
                        sleep(10)
                except Exception:
                    print(f'{traceback.format_exc()}\n')
        quantity, last_quantity, percentage = self.get_quantity(amount_of_shares, trade_client)
        if amount_of_shares >= trade_client.sells:
            trailing = self.trailing_or_regular(trade_client, figi, average_price, amount_of_shares) #ставим трейлинг или нет?
            if trailing:
                return True
            orders_id = trade_client.create_stop_orders(figi, percentage, quantity, last_quantity, average_price)
            self.sell(trade_client,figi,orders_id, lot)
            self.close_all_positions(trade_client)
            return False
        # если акций не хватает на продажу лесенкой
        elif 1 <= amount_of_shares < trade_client.sells:
            print(f'Акций не хватает на продажу лесенкой. Продам через {trade_client.start_time} секунд')
            for _ in tqdm(range(trade_client.start_time)):
                sleep(1)
            trade_client.sell_by_figi(figi, quantity=amount_of_shares)
            self.close_all_positions(trade_client)
            return False