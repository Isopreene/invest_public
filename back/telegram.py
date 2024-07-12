from telethon.sync import TelegramClient
from telethon import functions
from telethon.tl.types import MessageMediaDocument, MessageService, MessageEntityCustomEmoji, MessageActionGroupCall
import re
from back.trade import Trading

class TelegramParsing:

    def __init__(self, private_channel_id, arguments_parsing, arguments_tg):
        self.private_channel_id = private_channel_id
        self.client = self.create_tg_client(**arguments_tg)
        self.arguments_parsing = arguments_parsing

    def search_first_sentence(self, messages):
        messages = map(lambda message: [re.search('.*?[\.!\?](?:\s|$)', message[0]).group(0) if \
                                        re.search('.*?[\.!\?](?:\s|$)', message[0]) else message[0][:100],
                                        message[1],
                                        message[2]], messages)
        return messages

    def filter(self, new_message, text_for_search, text_for_ban, emoji_filter):
        filtered_message = list(filter(lambda message:
                                        message[-1] and all(key_phrase not in message[0] for key_phrase in
                                                            text_for_ban) and emoji_filter == set(
                                            x.document_id for x in message[-1]
                                            if isinstance(x, MessageEntityCustomEmoji)) or
                                        message and not isinstance(message[1], MessageMediaDocument) and
                                        any(key_phrase in message[0] for key_phrase in text_for_search) and
                                        all(key_phrase not in message[0] for key_phrase in text_for_ban),
                                        self.search_first_sentence(new_message)))
        if filtered_message:
            filtered_message = list(map(lambda x: x[0], new_message))
        return filtered_message

    @staticmethod
    def create_tg_client(api_hash, api_id, phone, device_model, app_version, system_version,
                         lang_code):
        client = TelegramClient('session', api_id, api_hash,
                                device_model=device_model, app_version=app_version,
                                system_version=system_version, lang_code=lang_code)
        client.start(phone=phone)
        return client

    def get_post_for_trading(self, trade_client: Trading):
        client = self.client
        filtered_message = ''
        with client:
            unread = int(
                client(functions.messages.GetPeerDialogsRequest(peers=[self.private_channel_id])).dialogs[0].unread_count)
            if unread:
                new_message = [x for x in
                                client.iter_messages(entity=self.private_channel_id,
                                                     limit=1)]
                if isinstance(new_message[0], MessageService):
                    # trade_client.use_lev = not trade_client.use_lev
                    # print(f'Обнаружен MessageService, use_lev сменили на {trade_client.use_lev}')
                    pass
                else:
                    new_message = [[new_message[0].message.lower(),
                                   new_message[0].media,
                                   new_message[0].entities]]
                    filtered_message = self.filter(new_message, **self.arguments_parsing)
                    if not filtered_message:
                        print(f'new message but no signal {list(map(lambda x: x[0][:100], new_message))}')
                    else:
                        print(f'new signal {list(map(lambda x: x[0][:100], new_message))}')
                client.send_read_acknowledge(self.private_channel_id)
                return filtered_message[0] if filtered_message else filtered_message
            return ''

