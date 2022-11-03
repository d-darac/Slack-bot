import logging
from datetime import datetime
import os
from dotenv import load_dotenv, find_dotenv

from slack_config import slack_client, slack_errors
from slack_response import SlackResponse

logging.basicConfig(level=logging.INFO)


class BaseMessage:
    def __init__(
        self,
        config: dict,
        oldest_date: str,
        latest_date: str,
        utc_offset: str,
        slack_user_id: str,
    ):
        self._slack_client = slack_client
        self._slack_user_id = slack_user_id
        self._config = config
        self._oldest_timestamp = self._convert_date_to_timestamp(oldest_date)
        self._latest_timestamp = self._convert_date_to_timestamp(latest_date)
        self._channel_messages = []
        self._utc_offset = utc_offset

        try:
            conversation = self._slack_client.conversations_history(
                channel=self._config["channel_id"],
                limit=100,
                oldest=self._oldest_timestamp,
                latest=self._latest_timestamp,
                inclusive=True,
            )

            ignore_subtypes = [
                "bot_message",
                "me_message",
                "channel_join",
                "channel_leave",
                "channel_topic",
                "channel_purpose",
                "channel_name",
                "channel_archive",
                "channel_unarchive",
                "file_share",
                "channel_posting_permissions",
            ]

            if conversation["messages"]:
                for message in conversation["messages"]:
                    if ("subtype" in message) and (
                        message["subtype"] in ignore_subtypes
                    ):
                        continue

                    consult_message = self._convert_slack_message_to_consult_message(
                        message, self._config, self._utc_offset
                    )
                    self._channel_messages.append(consult_message)

                while conversation["has_more"]:
                    conversation = self._slack_client.conversations_history(
                        channel=self._config["channel_id"],
                        limit=100,
                        cursor=conversation["response_metadata"]["next_cursor"],
                    )
                    for message in conversation["messages"]:
                        if ("subtype" in message) and (
                            message["subtype"] in ignore_subtypes
                        ):
                            continue

                        consult_message = (
                            self._convert_slack_message_to_consult_message(
                                message, self._config, self._utc_offset
                            )
                        )
                        self._channel_messages.append(consult_message)

        except slack_errors.SlackApiError:
            logging.exception(f"Exception while fetching messages")

            response = SlackResponse(
                channel_id=self._config["channel_id"],
                slack_user_id=slack_user_id,
                status=":aaaaaaaa: Failed request - server error",
                message="Something went awry!",
            )
            response.send()

        except Exception:
            logging.exception(f"Exception during class instantiation")

            response = SlackResponse(
                channel_id=self._config["channel_id"],
                slack_user_id=slack_user_id,
                status=":aaaaaaaa: Failed request - server error",
                message="Something went awry!",
            )
            response.send()

    def _convert_slack_message_to_consult_message(
        self, slack_message: dict, config: dict, utc_offset: str
    ) -> dict:
        tz_info = datetime.strptime(utc_offset, "%z").tzinfo

        load_dotenv(find_dotenv())

        consult_message = {
            "created": datetime.fromtimestamp(
                float(slack_message["ts"]), tz_info
            ).strftime("%d/%m/%Y %H:%M:%S %Z"),
            "has_ping_word": False,
            "is_handled": False,
            "topic": None,
            "research": None,
            "slack_link": f"https://{os.environ['WORKSPACE']}.slack.com/archives/{config['channel_id']}/p{str(slack_message['ts']).replace('.', '')}",
            "handled_by": {},
        }

        if any(
            message_ping_word.lower()
            in ("".join(slack_message["text"].split()).lower())
            for message_ping_word in config["channel_ping_words"]
        ):
            consult_message["has_ping_word"] = True

        if ("reactions" in slack_message) and ("reply_users" in slack_message):
            if any(
                name == config["reaction_for_handling"]
                for name in [
                    reaction["name"] for reaction in slack_message["reactions"]
                ]
            ):
                for reaction in slack_message["reactions"]:
                    if reaction["name"] == config["reaction_for_handling"]:
                        for reaction_user in reaction["users"]:
                            if reaction_user == slack_message["user"]:
                                break

                            if (reaction_user in slack_message["reply_users"]) and (
                                reaction_user in config["consult_agent_ids"]
                            ):
                                try:
                                    consult_agent = self._slack_client.users_info(
                                        user=reaction_user
                                    )
                                    consult_message["handled_by"][
                                        "name"
                                    ] = consult_agent["user"]["profile"]["real_name"]
                                    consult_message["handled_by"][
                                        "email"
                                    ] = consult_agent["user"]["profile"]["email"]

                                    consult_message["is_handled"] = True

                                except slack_errors.SlackApiError:
                                    logging.exception(
                                        f"Error fetching Slack user: {reaction_user}"
                                    )

                                if not consult_message["topic"]:
                                    consult_message["topic"] = "valid"

                                if not consult_message["research"]:
                                    consult_message["research"] = "provided"

                    if reaction["name"] == config["reaction_for_invalid"]:
                        consult_message["topic"] = "invalid"

                    if reaction["name"] == config["reaction_for_no_research"]:
                        consult_message["research"] = "none"

        return consult_message

    def _convert_date_to_timestamp(self, date_string):
        if date_string:
            for format in (
                "%d%b%Y",
                "%d%b%Y,%z",
                "%d%b%Y,%H:%M",
                "%d%b%Y,%H:%M%z",
                "%d%b%Y,%H:%M:%S",
                "%d%b%Y,%H:%M:%S%z",
                "%d%B%Y",
                "%d%B%Y,%z",
                "%d%B%Y,%H:%M",
                "%d%B%Y,%H:%M%z",
                "%d%B%Y,%H:%M:%S",
                "%d%B%Y,%H:%M:%S%z",
                "%d/%m/%Y",
                "%d/%m/%Y,%z",
                "%d/%m/%Y,%H:%M",
                "%d/%m/%Y,%H:%M%z",
                "%d/%m/%Y,%H:%M:%S",
                "%d/%m/%Y,%H:%M:%S%z",
                "%d.%m.%Y",
                "%d.%m.%Y,%z",
                "%d.%m.%Y,%H:%M",
                "%d.%m.%Y,%H:%M%z",
                "%d.%m.%Y,%H:%M:%S",
                "%d.%m.%Y,%H:%M:%S%z",
                "%d-%m-%Y",
                "%d-%m-%Y,%z",
                "%d-%m-%Y,%H:%M",
                "%d-%m-%Y,%H:%M%z",
                "%d-%m-%Y,%H:%M:%S",
                "%d-%m-%Y,%H:%M:%S%z",
            ):
                try:
                    return datetime.strptime(date_string, format).timestamp()
                except ValueError:
                    pass

            raise ValueError("Invalid date format")

        else:
            return None
