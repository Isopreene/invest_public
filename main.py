from back.work import Work
import schedule
from time import sleep
import os

if __name__ == '__main__':

    debug = os.getenv("DEBUG", 'True').lower() in ('true', '1', 't')
    manual = os.getenv("MANUAL", 'True').lower() in ('true', '1', 't')

    # Инициализация объектов классов Trading, TelegramParser и GPT в объекте класса Work. Не нужно создавать каждый раз
    mech = Work(debug=debug, manual=manual)
    if debug:
        print('Запуск в режиме отладки. Тестируем...')
    else:
        print('Запуск в рабочем режиме. Поехали!')
    if manual:
        print('Запуск торговли в ручном режиме')
    else:
        print('Запуск торговли в обычном режиме')
    file = schedule.every().day.at("05:00", tz='Europe/Moscow').do(mech.update_db)
    schedule.every().day.at("12:00", tz='Europe/Moscow').do(mech.set_lev_false)
    while True:
        schedule.run_pending()
        mech.main_program()
        sleep(0.5)