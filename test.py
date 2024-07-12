from tinkoff.invest.utils import quotation_to_decimal, decimal_to_quotation
from back import trade, telegram
from telethon.sync import TelegramClient
from tinkoff.invest import (Client)
from time import sleep
from telethon.tl.types import MessageMediaDocument, MessageService, MessageEntityCustomEmoji, MessageActionGroupCall
from decimal import Decimal
from datetime import datetime, time, timedelta, timezone

"""Регулируем только эти строки"""
token = 't._H5b7ssnspFxgx1JVyIi2Eb1m8hj1B02S5-oyP6XAWzK00TFu_Lcn6zvFhKo0bFYZFUkq0IahIQvcdi8VkkXdA'
# token = 't.Wi3iCPJn9mGbJsCwQUfiYbp7wYXORLszBDqZuiz-fiig_cl22ya4eN9_xFv_rdem1VxAj-ex2zH1RzSBNHDysA'
figi = "BBG004730ZJ9"
arguments_tg = {'api_hash': '1b8df04d35d2a01ffc37eaed62df50b4', 'api_id': 27505732,
                # 'private_channel_id': 'testparsing14',
                'private_channel_id': -1001791362034,
                'device_model': "MacBook Pro M1 Pro",
                'app_version': "14.2.1",
                'system_version': "appVersion=10.7 (259026) BETA",
                'lang_code': "ru",
                'phone': '+79963546774'}


class Test:
    token = token
    figi = figi
    api_id = arguments_tg['api_id']
    api_hash = arguments_tg['api_hash']
    private_channel_id = arguments_tg['private_channel_id']
    device_model = arguments_tg['device_model']
    app_version = arguments_tg['app_version']
    system_version = arguments_tg['system_version']
    lang_code = arguments_tg['lang_code']

    def __init__(self):
        self.acc = self.get_acc()
        self.trader = trade.Trading(self.token)

    def show_info_trade(self):
        print(self.trader.show_portfolio())
        print(self.trader.show_balance())
        print(self.trader.show_portfolio_user())
        history = self.trader.get_history()
        print(*history, sep='\n')

    def get_acc(self):
        with Client(self.token) as client:
            # checking account id
            acc = client.users.get_accounts().accounts[0].id
            return acc

    def show_info_telegram(self):
        client = TelegramClient('session', self.api_id, self.api_hash,
                                device_model=self.device_model, app_version=self.app_version,
                                system_version=self.system_version, lang_code=self.lang_code)
        with client:
            new_messages = [[x.date, issubclass(MessageActionGroupCall, x.__class__)]
                            for x in client.iter_messages(self.private_channel_id, limit=100)
                            if isinstance(x, MessageService)]
            #client.send_read_acknowledge(self.private_channel_id)
            return new_messages

    def trailing(self):
        last_price = self.trader.get_last_price(figi, dec=True)
        resp = self.trader.create_trailing_stop(figi, quantity=1, last_price=last_price)
        return resp


    def get_history(self, figi=""):

        with Client(self.token) as client:
            history = client.operations.get_operations(account_id=self.acc, figi=figi,
                                                       ).operations
            history = filter(lambda x: x.type != 'Удержание комиссии за операцию', history)
            history = map(lambda x: dict(date=(x.date + timedelta(hours=3)).strftime('%d.%m.%y.%H:%M:%S'),
                                         type=x.type,
                                         payment=x.payment.units,
                                         quantity=x.quantity,
                                         figi=x.figi
                                         ), history)
        return history


t = Test()
t.show_info_trade()