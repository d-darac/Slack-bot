import threading
import time
import logging
import os
import json

from slack_config import slack_client
from consult_message import ConsultMessage
from util import extract_dates_from_string, check_config
from slack_response import SlackResponse


def run_confing_command(
    command: dict,
    slack_user_id: str,
    slack_channel_id: str,
) -> None:
    kwargs = {
        "command": command,
        "slack_user_id": slack_user_id,
        "slack_channel_id": slack_channel_id,
    }

    threading.Thread(target=_config_command_background_task, kwargs=kwargs).start()


def run_report_command(
    command: dict,
    slack_user_id: str,
    config: dict,
) -> None:
    kwargs = {
        "command": command,
        "slack_user_id": slack_user_id,
        "config": config,
    }

    threading.Thread(target=_report_command_background_task, kwargs=kwargs).start()


def _report_command_background_task(
    command: dict, slack_user_id: str, config: dict
) -> None:
    try:
        if command["name"] == "formats":
            response = SlackResponse(
                channel_id=config["channel_id"],
                slack_user_id=slack_user_id,
            )

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Supported date formats*:\n\t• dd mmmm yyyy - e.g. 01 January 2022\n\t• dd mmm yyyy - e.g. 01 Jan 2022\n\t• dd/mm/yyyy - e.g. 01/01/2022\n\t• dd.mm.yyyy - e.g. 01.01.2022\n\t• dd-mm-yyyy - e.g. 01-01-2022",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Supported time formats (24 hour system only):*\n\t• hh:mm - e.g. 13:37\n\t• hh:mm:ss - e.g. 04:20:20",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Supported offset formats:*\n\t• [+/-]hhmm - e.g. +0100\n\t• [+/-]hh:mm - e.g. -07:00",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "You can include a specific time of day as well as a UTC time offset. If included, it must come after the date, separated with a single comma.\n\nYou can include the ofsset without the time, and the time without the ofsset, but if both are included the offset must come after the time.\n\nWhen specifying a date range (i.e. 'from 01/01/2022 to 31/01/2022'), note that you can include the offset after both dates, however only the first offset will be taken into consideration.",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Examples:*\n\t• /consults all on 01/01/2022, +0100\n\t• /consults all from 01/01/2022, 00:00 to 01/01/2022, 23:59:59\n\t• /consults all from 01/01/2022, 08:00 to 01/01/2022, 04:30 +01:00",
                    },
                },
            ]

            response.set_custom_message_blocks(blocks)
            return response.send()

        date_time_list = extract_dates_from_string(command["args"]["date_time"])
        current_time = time.time()

        def check_argument_and_create_csv():
            if command["name"] == "all":
                messages = consult_message.all_messages()

                return consult_message.generate_csv(
                    messages, f"all_consults_{current_time}.csv"
                )

            if command["name"] == "handled":
                messages = consult_message.handled_messages()

                return consult_message.generate_csv(
                    messages, f"handled_consults_{current_time}.csv"
                )

            if command["name"] == "unhandled":
                messages = consult_message.unhandled_messages()

                return consult_message.generate_csv(
                    messages, f"unhandled_consults_{current_time}.csv"
                )

            if command["name"] == "with-ping-word":
                messages = consult_message.messages_with_ping_word()

                return consult_message.generate_csv(
                    messages, f"consults_with_ping_word_{current_time}.csv"
                )

        if len(date_time_list) == 1:
            consult_message = ConsultMessage(
                config,
                oldest_date=f"{date_time_list[0]['date']},{date_time_list[0]['time'] or '00:00'}{date_time_list[0]['time_zone'] or '+0000'}",
                latest_date=f"{date_time_list[0]['date']},{date_time_list[0]['time'] or '23:59:59'}{date_time_list[0]['time_zone'] or '+0000'}",
                utc_offset=date_time_list[0]["time_zone"] or "+0000",
                slack_user_id=slack_user_id,
            )

            report = check_argument_and_create_csv()

            if report["is_empty"]:
                response = SlackResponse(
                    channel_id=config["channel_id"],
                    slack_user_id=slack_user_id,
                    status=":question: Failed request - not found",
                    message="No data found based on given parameters. Please adjust your parameters and try again",
                )

                return response.send()

            response = SlackResponse(
                channel_id=config["channel_id"],
                slack_user_id=slack_user_id,
                message=f"Your report is ready, download it by clicking <{report['url']}|this link>",
            )

            return response.send()

        if len(date_time_list) == 2:
            consult_message = ConsultMessage(
                config,
                oldest_date=f"{date_time_list[0]['date']},{date_time_list[0]['time'] or '00:00'}{date_time_list[0]['time_zone'] or '+0000'}",
                latest_date=f"{date_time_list[1]['date']},{date_time_list[1]['time'] or '23:59:59'}{date_time_list[1]['time_zone'] or '+0000'}",
                utc_offset=date_time_list[0]["time_zone"]
                or date_time_list[1]["time_zone"]
                or "+0000",
                slack_user_id=slack_user_id,
            )

            report = check_argument_and_create_csv()

            if report["is_empty"]:
                response = SlackResponse(
                    channel_id=config["channel_id"],
                    slack_user_id=slack_user_id,
                    status=":question: Failed request - not found",
                    message="No data found based on given parameters. Please adjust your parameters and try again",
                )

                return response.send()

            response = SlackResponse(
                channel_id=config["channel_id"],
                slack_user_id=slack_user_id,
                message=f"Your report is ready, download it by clicking <{report['url']}|this link>",
            )

            return response.send()

    except ValueError:
        logging.exception(f"Exception occured while converting date to timestamp")

        response = SlackResponse(
            channel_id=config["channel_id"],
            slack_user_id=slack_user_id,
            status=":x: Failed request - invalid",
            message="Unsupported date format. To view accepted date formats use: /consults formats",
        )

        response.send()

    except Exception:
        logging.exception(f"Exception during run_command")

        response = SlackResponse(
            channel_id=config["channel_id"],
            slack_user_id=slack_user_id,
            status=":aaaaaaaa: Failed request - server error",
            message="Something went awry!",
        )

        response.send()


def _config_command_background_task(
    command: str,
    slack_user_id: str,
    slack_channel_id: str,
) -> None:
    try:
        if command["name"] == "help":
            response = SlackResponse(
                channel_id=slack_channel_id,
                slack_user_id=slack_user_id,
            )

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*get* - used to retrieve the current channel configuration\n*set* - used to set property values\n*delete* - used to remove values from array properties",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Supported arguments for 'set' command:*\n\t• --channel_ping_words\n\t• --consult_agent_ids\n\t• --reaction_for_handling\n\t• --reaction_for_invalid\n\t• --reaction_for_no_research",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Supported arguments for 'delete' command:*\n\t• --channel_ping_words\n\t• --consult_agent_ids",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Examples:*\n\t• /consult-config set --channel_ping_words=WAT, SERVHELP\n\t• /consult-config set --reaction_for_handling=eyes --reaction_for_invalid=o\n\t• /consult-config delete --consult_agent_ids=U04691SKW3W\n\t• /consult-config delete --consult_agent_ids=U04691SKW3W, U0102HQB37Y",
                    },
                },
            ]

            response.set_custom_message_blocks(blocks)
            return response.send()

        if not os.path.isdir(f"./channels/{slack_channel_id}"):
            os.mkdir(f"./channels/{slack_channel_id}")
            os.mkdir(f"./channels/{slack_channel_id}/reports")

        if not os.path.isfile(f"./channels/{slack_channel_id}/config.json"):
            new_file = open(f"channels/{slack_channel_id}/config.json", "w")

            data = {
                "channel_id": slack_channel_id,
                "channel_ping_words": [],
                "consult_agent_ids": [],
                "reaction_for_handling": None,
                "reaction_for_invalid": None,
                "reaction_for_no_research": None,
            }

            json.dump(data, new_file, indent=4)
            new_file.close()

        with open(f"channels/{slack_channel_id}/config.json", "r") as config_file:
            config_as_dict: dict[str, list | str | dict] = json.load(config_file)

        if command["name"] == "get":
            response = SlackResponse(
                channel_id=slack_channel_id,
                slack_user_id=slack_user_id,
                message=json.dumps(config_as_dict, indent=4),
            )

            return response.send()

        if command["name"] == "delete":
            if "channel_ping_words" in command["args"]:
                values = command["args"]["channel_ping_words"]

                for v in values:
                    try:
                        config_as_dict["channel_ping_words"].remove(v)
                    except ValueError:
                        logging.exception(f"Exception during run_command")

                        response = SlackResponse(
                            channel_id=slack_channel_id,
                            slack_user_id=slack_user_id,
                            status=":question: Failed request - not found",
                            message=f"No such ping word: {v}",
                        )

                        return response.send()

            elif "consult_agent_ids" in command["args"]:
                values = command["args"]["consult_agent_ids"]

                for v in values:
                    try:
                        config_as_dict["consult_agent_ids"].remove(v)
                    except ValueError:
                        logging.exception(f"Exception during run_command")

                        response = SlackResponse(
                            channel_id=slack_channel_id,
                            slack_user_id=slack_user_id,
                            status=":question: Failed request - not found",
                            message=f"No such user ID: {v}",
                        )

                        return response.send()

            with open(f"channels/{slack_channel_id}/config.json", "w") as config_file:
                json.dump(config_as_dict, config_file, indent=4)

            response = SlackResponse(
                channel_id=slack_channel_id,
                slack_user_id=slack_user_id,
                message="Values removed.",
            )

            return response.send()

        if command["name"] == "set":
            if "channel_ping_words" in command["args"]:
                values = command["args"]["channel_ping_words"]
                for v in values:
                    config_as_dict["channel_ping_words"].append(v)

            if "consult_agent_ids" in command["args"]:
                values = command["args"]["consult_agent_ids"]
                for v in values:
                    config_as_dict["consult_agent_ids"].append(v)

            if "reaction_for_handling" in command["args"]:
                config_as_dict["reaction_for_handling"] = command["args"][
                    "reaction_for_handling"
                ]

            if "reaction_for_invalid" in command["args"]:
                config_as_dict["reaction_for_invalid"] = command["args"][
                    "reaction_for_invalid"
                ]

            if "reaction_for_no_research" in command["args"]:
                config_as_dict["reaction_for_no_research"] = command["args"][
                    "reaction_for_no_research"
                ]

            with open(f"channels/{slack_channel_id}/config.json", "w") as config_file:
                json.dump(config_as_dict, config_file, indent=4)

            config = check_config(slack_channel_id)

            if config["empty_keys"]:
                response = SlackResponse(
                    channel_id=slack_channel_id,
                    slack_user_id=slack_user_id,
                    message=f"Properties left to configure: {', '.join(config['empty_keys'])}",
                )

                return response.send()

            else:
                response = SlackResponse(
                    channel_id=slack_channel_id,
                    slack_user_id=slack_user_id,
                    message="All properties configured. The bot is ready to be used in this channel.",
                )

                return response.send()

    except Exception:
        logging.exception(f"Exception during run_command")

        response = SlackResponse(
            channel_id=slack_channel_id,
            slack_user_id=slack_user_id,
            status=":aaaaaaaa: Failed request - server error",
            message="Something went awry!",
        )

        response.send()
