from decimal import Decimal

parsing_parameters = dict(arguments_parsing=dict(text_for_search=['покупаю акции', 'беру в лонг', 'беру в среднесрочный лонг',
                                           'покупаю на среднесрок акции', 'беру во внутри дневной лонг акции',
                                           'беру внутри дня спекулятивно в лонг акции', 'покупаю лесенкой',
                                           'беру в лонг спекулятивно',
                                           'беру в краткосрочный лонг',
                                            'докупаю акции'],
                          text_for_ban=['шорт', 'sber', 'lkoh', 'vtbr',
                                        'gazp', 'nsvz', 'mstt', 'elfv', 'abrd',
                                        'rkke', 'krknp', 'life', 'blng',
                                        'kzosp', 'krot'],

                          emoji_filter={5332653943291918474, 5330101079155684836,
                                        5330199760324280035, 5330097479973093431,
                                        5330530790633648414,
                                        })) # id каждой нужной эмодзи
telegram_parameters = dict(api_hash='API_HASH',
                           api_id='API_ID',
                           phone='PHONE',
                           device_model="MacBook Pro M1 Pro",
                           app_version="14.2.1",
                           system_version="appVersion=10.7 (259026) BETA",
                           lang_code="ru",
                           )

working_parameters = dict(arguments_tg=telegram_parameters,
                          private_channel_id='CHANNEL ID',
                          arguments_trade = dict(token='TOKEN',
                                                 second_token='',
                                                 money=100000,
                                                 sells=10,
                                                 use_lev=False,
                                                 start_time=40,
                                                 sleeping_time=20,
                                                 start_percent=round(Decimal(0.2), 2),
                                                 finish_percent=round(Decimal(1.1), 2)))

test_parameters = dict(arguments_tg=telegram_parameters,
                       private_channel_id='TEST CHANNEL ID',
                       arguments_trade = dict(
                           token='TOKEN',
                           second_token='',
                           money=4000,
                           sells=10,
                           use_lev=False,
                           start_time=10,
                           sleeping_time=10,
                           start_percent=round(Decimal(0.2), 2),
                           finish_percent=round(Decimal(1.1), 2)))


gpt_parameters = dict(api_key = "API_KEY_GPT",
                      model = "gpt-4-turbo-preview",
                      description = f"Переключись на русский. Ты ассистент на фондовой бирже. "
                                      f"Найди название акционерной компании в тексте. "
                                      f"Сравни это название со строками name в json-файле. "
                                      f"Выведи только наиболее совпадающую "
                                      f"строку name в формате «company:name» без пояснений")

shares_to_add = [{"ticker": "HNFG",
                  "name": "хендерсон",
                  "figi": "TCS00A106XF2",
                  "lot": 1},
                 {"ticker": "SBER",
                  "name": "сбер",
                  "figi": "BBG004730N88",
                  "lot": 10},
                 {"ticker": "GECO",
                  "name": "цгрм генетико",
                  "figi": "TCS00A105BN4",
                  "lot": 10
                  },
                 {"ticker": "GECO",
                  "name": "цгрм",
                  "figi": "TCS00A105BN4",
                  "lot": 10
                  },
                 {
                     "ticker": "HHRU",
                     "name": "headhunter",
                     "figi": "TCS2207L1061",
                     "lot": 1
                 },
                 {
                     "ticker": "VTBR",
                     "name": "втб",
                     "figi": "BBG004730ZJ9",
                     "lot": 10000
                 },
                 {
                     "ticker": "GMKN",
                     "name": "гмк",
                     "figi": "BBG004731489",
                     "lot": 1
                 },
                 {
                     "ticker": "GMKN",
                     "name": "норникель",
                     "figi": "BBG004731489",
                     "lot": 1
                 },
                 {
                     "ticker": "POLY",
                     "name": "полиметалл",
                     "figi": "BBG004PYF2N3",
                     "lot": 1
                 },
                 ]

