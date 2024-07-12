import tinkoff.invest as ti
from tinkoff.invest import (Client, StopOrderDirection, InstrumentIdType,
                            StopOrderExpirationType, StopOrderType, MoneyValue, ExchangeOrderType,
                            StopOrderTrailingData, TakeProfitType)
from tinkoff.invest.utils import quotation_to_decimal, decimal_to_quotation, money_to_decimal
from tinkoff.invest.exceptions import RequestError
from decimal import Decimal
import datetime
from time import sleep
from tinkoff.invest.exceptions import RequestError
from tinkoff.invest.schemas import TrailingValueType
class Trading:

    def __init__(self, token:str, second_token:str='', money:int =0, sells:int=0, use_lev:bool=False, start_time:int=0,
                 sleeping_time:int=0, start_percent:Decimal=0, finish_percent:Decimal=0):
        self.token = token
        self.second_token = second_token
        self.money = money
        self.sells = sells
        self.use_lev = use_lev
        self.start_time = start_time
        self.sleeping_time = sleeping_time
        self.start_percent = start_percent
        self.finish_percent = finish_percent
        self.acc = self.get_acc()


    def get_all_stocks(self):
        with Client(self.token) as client:
            r = client.instruments.shares()
        return r

    def get_acc(self):
        with Client(self.token) as client:
            # checking account id
            acc = client.users.get_accounts().accounts[0].id
            return acc

    def buy_by_figi(self, figi:str, lot:int, money:int|float, quantity:int|float=0):
        with Client(self.token) as client:
            #  checking last price
            if not quantity:
                last_price = (
                    client.market_data.get_last_prices(figi=[figi]).last_prices[0].price
                )
                last_price = float(quotation_to_decimal(last_price))
                quantity = int(money / (last_price * lot))  # минимальное количество для покупки
            if quantity > 0:
                #  order_to_buy
                response = client.orders.post_order(figi=figi,
                                         quantity=quantity,
                                         order_type=ti.OrderType.ORDER_TYPE_MARKET,
                                         direction=ti.OrderDirection.ORDER_DIRECTION_BUY,
                                         account_id=self.acc)
                return response
        return

    def sell_by_figi(self, figi:str, quantity:int|float=0):
        with Client(self.token) as client:
            if quantity > 0:
                # order_to_sell
                response = client.orders.post_order(figi=figi,
                                                    quantity=quantity,
                                                    order_type=ti.OrderType.ORDER_TYPE_MARKET,
                                                    direction=ti.OrderDirection.ORDER_DIRECTION_SELL,
                                                    account_id=self.acc)
                return response


    def create_stop_orders(self, figi, percentage, quantity, last_quantity, average_price:Decimal) -> dict:
        """Выставляет стоп-ордера и выдаёт словарь с выставленными ордерами, их id и процентами"""
        # выставляем стоп-ордера на продажу в количестве sells-1
        orders_id = dict()
        for i in range(0, self.sells - 1):
            sleep(0.5)
            profit_percentage = self.start_percent + percentage * i
            order_id = self.sell_stop_order(figi, quantity, profit_percentage, average_price)
            orders_id.update({order_id: [i, quantity, profit_percentage]})
        # ставим ещё 1 ордер, чтобы всего было sells штук
        order_id = self.sell_stop_order(figi, last_quantity, self.finish_percent, average_price)
        orders_id.update({order_id: [self.sells - 1, last_quantity, self.finish_percent]})
        if len(orders_id) == self.sells:
            print('Стоп-ордера выставлены')
        else:
            print('Стоп-ордера не выставлены, что-то пошло не так')
        return orders_id


    def get_last_price(self, figi, dec=False):
        for _ in range(3):
            try:
                with Client(self.token) as client:
                    last_price = client.market_data.get_last_prices(figi=[figi]).last_prices[0].price
                if dec:
                    last_price = quotation_to_decimal(last_price)
                return last_price
            except RequestError:
                sleep(1)

    def sell_stop_order(self, figi: str, quantity: int | float = 0,
                        profit_percentage: Decimal = 0, last_price=Decimal(0)):
        with Client(self.token) as client:
            direction = StopOrderDirection.STOP_ORDER_DIRECTION_SELL
            stop_order_type = StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT
            exp_type = StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
            exchange_order_type = ExchangeOrderType.EXCHANGE_ORDER_TYPE_LIMIT
            stop_price = self.convert_price(figi, profit_percentage, last_price)
            #  checking last price
            if quantity > 0:
                #  post_order_to_buy
                stop_order_id = client.stop_orders.post_stop_order(figi=figi,
                                                                   quantity=quantity,
                                                                   price=stop_price,
                                                                   stop_price=stop_price,
                                                                   direction=direction,
                                                                   account_id=self.acc,
                                                                   expiration_type=exp_type,
                                                                   stop_order_type=stop_order_type,
                                                                   exchange_order_type=exchange_order_type,
                                                                   )
                return stop_order_id.stop_order_id
    def get_price_with_increment(self, figi, price):
        with Client(self.token) as client:
            price = Decimal(price)
            min_price_increment = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi
            ).instrument.min_price_increment
            min_price_increment = quotation_to_decimal(min_price_increment)
            price = (round(price / min_price_increment) * min_price_increment)
            return price

    def show_balance(self):
        with Client(self.token) as client:
            balance = client.operations.get_portfolio(account_id=self.acc).total_amount_currencies.units
            return balance

    def show_portfolio_user(self):
        portfolio = self.show_portfolio()
        if portfolio:
            return ' '.join(map(lambda x: f'{x.figi} – {x.balance} шт', portfolio))
        return 'Акций на балансе нет'

    def show_portfolio(self):
        with Client(self.token) as client:
            portfolio = client.operations.get_positions(account_id=self.acc).securities
            return portfolio


    def get_margin(self):
        with Client(self.token) as client:
            margin = client.users.get_margin_attributes(account_id=self.acc)
        return margin

    def get_info_client(self):
        with Client(self.token) as client:
            margin = client.users.get_info_client()
        return margin

    def get_history(self, figi=""):

        with Client(self.token) as client:
            history = client.operations.get_operations(account_id=self.acc, figi=figi,
                                                       from_=datetime.datetime.now().replace(hour=0,
                                                                                             minute=0,
                                                                                             second=0,
                                                                                             microsecond=0)).operations
            history = filter(lambda x: x.type != 'Удержание комиссии за операцию', history)
            history = map(lambda x: dict(date=(x.date + datetime.timedelta(hours=3)).strftime('%H:%M:%S'),
                                         type=x.type,
                                         payment=x.payment.units,
                                         quantity=x.quantity,
                                         figi=x.figi
                                         ), history)
        return history

    def get_leverage_by_figi(self, figi):
        with Client(self.token) as client:
            share = client.instruments.share_by(id_type=1, id=figi).instrument.dlong
        lev = 1
        if share.nano and not share.units:
            lev = round(1 / float(f'0.{share.nano}'), 1)
        return lev

    def get_stop_orders(self, figi=None, second_token=None) -> list:
        token = self.token if not second_token else self.second_token
        with Client(token) as client:
            resp = client.stop_orders.get_stop_orders(account_id=self.acc).stop_orders
        if figi:
            return [i.stop_order_id for i in resp if i and i.figi == figi]
        return [i.stop_order_id for i in resp if i]

    def cancel_stop_order(self, order_id):
        with Client(self.token) as client:
            try:
                response = client.stop_orders.cancel_stop_order(account_id=self.acc, stop_order_id=order_id)
                return response
            except Exception as e:
                return e

    def cancel_limit_order(self, order_id):
        with Client(self.token) as client:
            try:
                response = client.orders.cancel_order(account_id=self.acc, order_id=order_id)
                return response
            except Exception as e:
                return f'Error: {e}'

    def convert_price(self, figi, percentage, price):
        stop_price = price * Decimal(str(round(1 + percentage / 100, 3)))
        stop_price = self.get_price_with_increment(figi, stop_price)
        stop_price = decimal_to_quotation(Decimal(stop_price))
        return stop_price

    def cancel_limit_orders(self) -> list:
        canceled_orders = []
        with Client(self.token) as client:
            resp = client.orders.get_orders(account_id=self.acc).orders
            for order in resp:
                r = client.orders.cancel_order(account_id=self.acc, order_id=order.order_id)
                canceled_orders.append(r)
            return canceled_orders

    def get_limit_orders(self, figi=None) -> list:
        with Client(self.token) as client:
            resp = client.orders.get_orders(account_id=self.get_acc()).orders
        if figi:
            return [(i.order_request_id, i.order_id) for i in resp if i and i.figi == figi]
        return [(i.order_request_id, i.order_id) for i in resp if i]

    def create_trailing_stop(self, figi: str, quantity: int | float = 0,
                        last_price=Decimal(0)):
        with Client(self.token) as client:
            direction = StopOrderDirection.STOP_ORDER_DIRECTION_SELL
            stop_order_type = StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT
            exp_type = StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
            trailing_price = decimal_to_quotation(Decimal(str(0.35)))
            trailing_data = StopOrderTrailingData(indent=trailing_price,
                                                  indent_type=TrailingValueType.TRAILING_VALUE_RELATIVE)
            #  checking last price
            if quantity > 0:
                #  post_order_to_buy
                stop_order_id = client.stop_orders.post_stop_order(figi=figi,
                                                                   quantity=quantity,
                                                                   price=last_price,
                                                                   stop_price=last_price,
                                                                   direction=direction,
                                                                   account_id=self.acc,
                                                                   expiration_type=exp_type,
                                                                   stop_order_type=stop_order_type,
                                                                   take_profit_type=TakeProfitType.TAKE_PROFIT_TYPE_TRAILING,
                                                                   exchange_order_type=ExchangeOrderType.EXCHANGE_ORDER_TYPE_MARKET,
                                                                   trailing_data=trailing_data
                                                                  )
                return stop_order_id.stop_order_id