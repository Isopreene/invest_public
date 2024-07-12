from back.funcs import Functions
from time import sleep
import traceback
from back.db_build import DBBuilder
from back.gpt import GPT
from back.telegram import TelegramParsing
from back.trade import Trading
from back.conditions import shares_to_add, gpt_parameters, parsing_parameters, test_parameters, working_parameters
class Work:

    def __init__(self, debug=False, manual=False):
        self.manual = manual
        self.params = self.parameters(debug)
        self.token = self.params.get('arguments_trade').get('token')
        self.gpt_client = None #GPT(**gpt_parameters)
        self.private_channel_id = self.params.get('private_channel_id')
        self.tg_client = TelegramParsing(self.private_channel_id, self.params.get('arguments_parsing'), self.params.get('arguments_tg'))
        self.trade_client = Trading(**self.params.get('arguments_trade'))
        self.worker = Functions()
        self.shares_to_add = shares_to_add
        self.old_balance = None
        if self.old_balance is None:
            self.old_balance = self.trade_client.show_balance()
        self.active_deal = 0

    @staticmethod
    def parameters(debug):
        if debug:
            return parsing_parameters | test_parameters
        return parsing_parameters | working_parameters

    def main_program(self):
        try:
            figi_and_lot = self.worker.parse(self.tg_client, self.gpt_client, self.trade_client)
            filtered_figi = figi_and_lot if figi_and_lot and figi_and_lot[0] and figi_and_lot[1] else []
            if filtered_figi:
                print(f'Найдено {filtered_figi}')
                if self.old_balance:
                    print(f'Оставшийся баланс: {self.old_balance} руб\n')
                active_deal = self.worker.buy_and_sell(filtered_figi, self.trade_client, manual=self.manual)
                try:
                    active_deal = int(active_deal)
                except TypeError:
                    active_deal = 0
                self.worker.send_read_acknowledge(self.tg_client, self.private_channel_id)
                if active_deal:
                    self.active_deal += active_deal
                    (self.trade_client.token,
                     self.trade_client.second_token) = (self.trade_client.second_token,
                                                        self.trade_client.token)
                else:
                    new_balance = self.worker.show_balance(self.trade_client)
                    print(f'продали полностью\nОставшийся баланс: {new_balance} руб\n'
                          f'Акции на счёте:{self.trade_client.show_portfolio_user()}\n'
                          f'Прибыль: {round((new_balance - self.old_balance) / self.old_balance, 4) * 100}%\n')
                    self.old_balance = new_balance
                if self.active_deal == 2:
                    while True:
                        orders1 = self.trade_client.get_stop_orders()
                        if not orders1:
                            "первый токен освободился"
                            self.trade_client.token, self.trade_client.second_token = (self.trade_client.second_token,
                                                                                       self.trade_client.token)
                            break
                        orders2 = self.trade_client.get_stop_orders(second_token=True)
                        if not orders2:
                            "второй токен освободился"
                            break
                        sleep(1)



            sleep(0.1)
        except Exception:
            print(f'{traceback.format_exc()}\n')
            sleep(5)

    def update_db(self):
        file = DBBuilder().create_and_update_db(self.trade_client, self.shares_to_add)
        print('База данных обновлена')
        return file

    def set_lev_false(self):
        self.trade_client.use_lev = False