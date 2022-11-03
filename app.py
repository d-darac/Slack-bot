import os
import logging
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, make_response, send_from_directory

from slack_config import slack_signature_verifier
from commands import run_report_command, run_confing_command
from util import (
    serialize_to_dict,
    check_config,
    get_config_command,
    get_consult_command,
)
from slack_response import SlackResponse

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO)

if not os.path.isdir("./channels"):
    os.mkdir("./channels")

app = Flask(__name__)

config_err_blocks = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Valid commands:*\n\t• get\n\t• set\n\t• delete\n\t• help",
        },
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "For more info use: /consult-config help",
        },
    },
]

consult_err_blocks = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Valid commands:* all, handled, unhandled, with-ping-word",
        },
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Accepted date range arguments:* 'from [date] to [date]', 'on [date]'",
        },
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Examples*:\n\t• All consults between two dates: /consults all from 01/01/2022 to 01/02/2022\n\t• Handled consults on a specific date: /consults handled on 01/01/2022",
        },
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "To view accepted date formats use: /consults formats",
        },
    },
]


@app.route("/consult_configs", methods=["POST"])
def create_channel_config():
    try:
        data_bytes = request.get_data()

        if not slack_signature_verifier.is_valid_request(data_bytes, request.headers):
            return make_response("Unauthorized request.", 403)

        if data_bytes:
            params = serialize_to_dict(data_bytes)

        if not "text" in params:
            response = SlackResponse(
                channel_id=params["channel_id"],
                slack_user_id=params["user_id"],
                status=":x: Failed request - invalid",
            )

            response.set_custom_message_blocks(config_err_blocks)

            return make_response(response.get_message_blocks(), 200)

        else:
            command = get_config_command(params["text"])
            run_confing_command(
                command,
                params["user_id"],
                params["channel_id"],
            )

            return make_response()

    except ValueError:
        logging.exception(f"Exception occured handling a POST request")

        response = SlackResponse(
            channel_id=params["channel_id"],
            slack_user_id=params["user_id"],
            status=":x: Failed request - invalid",
        )

        response.set_custom_message_blocks(config_err_blocks)

        return make_response(response.get_message_blocks(), 200)

    except IndexError:
        logging.exception(f"Exception occured handling a POST request")

        response = SlackResponse(
            channel_id=params["channel_id"],
            slack_user_id=params["user_id"],
            status=":x: Failed request - invalid",
        )

        response.set_custom_message_blocks(config_err_blocks)

        return make_response(response.get_message_blocks(), 200)

    except Exception:
        logging.exception(f"Exception occured handling a POST request")

        response = SlackResponse(
            channel_id=params["channel_id"],
            slack_user_id=params["user_id"],
            status=":aaaaaaaa: Failed request - server error",
            message="Something went awry!",
        )

        return make_response(response.get_message_blocks(), 200)


@app.route("/consults", methods=["POST"])
def create_report():
    try:
        data_bytes = request.get_data()

        if not slack_signature_verifier.is_valid_request(data_bytes, request.headers):
            return make_response("Unauthorized request.", 403)

        if data_bytes:
            params = serialize_to_dict(data_bytes)

        config = check_config(params["channel_id"])

        if not config["is_config_file"]:
            response = SlackResponse(
                channel_id=params["channel_id"],
                slack_user_id=params["user_id"],
                status=":question: Failed request - not found",
                message="No configuration found. You will need to configure the bot for this channel using the command: '/consult-config'.",
            )

            return make_response(response.get_message_blocks(), 200)

        if config["empty_keys"]:
            response = SlackResponse(
                channel_id=params["channel_id"],
                slack_user_id=params["user_id"],
                status=":x: Failed request - invalid",
                message=f"Missing configurations: {', '.join(config['empty_keys'])}",
            )

            return make_response(response.get_message_blocks(), 200)

        if not "text" in params:
            response = SlackResponse(
                channel_id=params["channel_id"],
                slack_user_id=params["user_id"],
                status=":x: Failed request - invalid",
            )

            response.set_custom_message_blocks(consult_err_blocks)

            return make_response(response.get_message_blocks(), 200)

        else:
            command = get_consult_command(params["text"])

            run_report_command(command, params["user_id"], config["data"])

            return make_response()

    except ValueError:
        logging.exception(f"Exception occured handling a POST request")

        response = SlackResponse(
            channel_id=params["channel_id"],
            slack_user_id=params["user_id"],
            status=":x: Failed request - invalid",
        )

        response.set_custom_message_blocks(consult_err_blocks)

        return make_response(response.get_message_blocks(), 200)

    except Exception:
        logging.exception(f"Exception occured handling a POST request")
        response = SlackResponse(
            channel_id=params["channel_id"],
            slack_user_id=params["user_id"],
            status=":aaaaaaaa: Failed request - server error",
            message="Something went awry!",
        )

        return make_response(response.get_message_blocks(), 200)


@app.route(f"/channels/<channel_id>/reports/<report_name>", methods=["GET"])
def get_report(channel_id, report_name):
    if not os.path.isfile(f"./channels/{channel_id}/reports/{report_name}"):
        return make_response("File not found", 404)

    return send_from_directory(
        f"./channels/{channel_id}/reports", report_name, as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True, port=os.environ["PORT"])
