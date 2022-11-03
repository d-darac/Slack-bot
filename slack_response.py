from slack_config import slack_client
from typing import List, Dict


class SlackResponse:
    def __init__(
        self,
        channel_id: str,
        slack_user_id: str,
        message: str = None,
        status: str = None,
    ) -> None:
        self._channel_id = channel_id
        self._slack_user_id = slack_user_id
        self._message = message
        self._status = status or ":white_check_mark: Successful request"
        self._message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": self._status,
                    "emoji": True,
                },
            },
        ]

        if message:
            self._message_blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self._message,
                    },
                },
            )

    def send(self) -> None:
        slack_client.chat_postEphemeral(
            channel=self._channel_id,
            user=self._slack_user_id,
            blocks=self._message_blocks,
        )

    def get_message_blocks(self) -> Dict[str, List[Dict]]:
        return {"blocks": self._message_blocks}

    def set_custom_message_blocks(self, blocks: List[Dict]) -> None:
        for block in blocks:
            self._message_blocks.append(block)
