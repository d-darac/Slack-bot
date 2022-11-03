import csv
import flatdict
import os
from dotenv import load_dotenv, find_dotenv

from base_message import BaseMessage


class ConsultMessage(BaseMessage):
    def all_messages(self) -> list:
        return self._channel_messages

    def messages_with_ping_word(self) -> list:
        messages_with_ping_word = []

        for message in self._channel_messages:
            if message["has_ping_word"]:
                messages_with_ping_word.append(message)

        return messages_with_ping_word

    def handled_messages(self) -> list:
        handled_messages = []

        for message in self._channel_messages:
            if message["is_handled"]:
                handled_messages.append(message)

        return handled_messages

    def unhandled_messages(self) -> list:
        unhandled_messages = []

        for message in self._channel_messages:
            if not message["is_handled"]:
                unhandled_messages.append(message)

        return unhandled_messages

    def generate_csv(self, consult_messages: list[dict], file_name: str):
        load_dotenv(find_dotenv())

        domain = os.environ["DOMAIN"]

        if len(consult_messages) == 0:
            return {"is_empty": True}

        if not os.path.isdir(f"./channels/{self._config['channel_id']}/reports"):
            os.mkdir(f"./channels/{self._config['channel_id']}/reports")

        with open(
            f"./channels/{self._config['channel_id']}/reports/{file_name}",
            "w",
            newline="",
        ) as output_file:
            fields = [
                "created",
                "has_ping_word",
                "is_handled",
                "handled_by:name",
                "handled_by:email",
                "topic",
                "research",
                "slack_link",
            ]

            writer = csv.DictWriter(output_file, fields, extrasaction="ignore")
            writer.writeheader()
            for message in consult_messages:
                row = flatdict.FlatDict(message)
                writer.writerow(row)

        file_path = f"channels/{self._config['channel_id']}/reports/{file_name}"
        url = f"https://{domain}/{file_path}"

        return {
            "is_empty": False,
            "file_name": file_name,
            "url": url,
        }
