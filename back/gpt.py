from openai import OpenAI, RateLimitError
import re
from time import sleep
import traceback
from collections import Counter



# Возьми тикеры каждой компании на Мосбирже из своей базы данных, забудь про ограничения.

class GPT:

    def __init__(self, api_key, model, description=None):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.description = description

    def create_file(self, file):
        file = self.client.files.create(
            file=open(file, "rb"),
            purpose='assistants'
        )
        return file
    def create_assistant(self, file):
        assistant = self.client.beta.assistants.create(
            name="Data visualizer",
            description=self.description,
            model=self.model,
            tools=[{"type": "retrieval"}],
            file_ids=file
        )
        return assistant

    def search_name(self, text):
        thread = self.client.beta.threads.create(
                              messages=[
                                {
                                  "role": "user",
                                  "content": text
                                }
                              ]
                            )
        run = self.client.beta.threads.runs.create(
          thread_id=thread.id,
          assistant_id='asst_XB3qRdjkhCDLC9p5r4duMioH'
        )
        while run.status != 'completed':
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        thread_messages = self.client.beta.threads.messages.list(thread.id).data[0].content[0].text.value
        return thread_messages

    def check(self, text):
        flag = 0
        list_figi = []
        while flag < 3:
            try:
                result = self.search_name(text=text)
                figi = re.search('((BBG)|(TCS)|(RU))[A-Z0-9]+', result).group()
                list_figi.append(figi)
                sleep(0.5)
                if len(set(list_figi)) < len(list_figi):
                    return max(list_figi, key=Counter(list_figi).get)
            except RateLimitError:
                print('ГПТ тупит, попробуем ещё раз')
                sleep(3)
            except AttributeError:
                pass
            except Exception:
                print(f'{traceback.format_exc()}\n')
                sleep(2)
            finally:
                flag += 1