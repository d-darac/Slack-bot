from urllib.parse import parse_qs
import re
import os
import json


def serialize_to_dict(data_bytes: bytes) -> dict:
    data_str = str(data_bytes, "utf-8")

    formatted_data_dict = parse_qs(data_str)

    data = {}

    for key, value in formatted_data_dict.items():
        if len(value) == 1:
            data[key] = value[0]
        else:
            data[key] = value

    return data


def find_keyword(word: str):
    return re.compile(r"\b({0})\b".format(word), flags=re.IGNORECASE).search


def check_config(slack_channel_id: str) -> dict:
    res = {"is_config_file": False, "data": {}, "empty_keys": []}

    if not os.path.isdir(f"./channels/{slack_channel_id}"):
        return res

    with open(f"./channels/{slack_channel_id}/config.json", "r") as file:
        config: dict = json.load(file)

    empty_keys = []

    for k, v in config.items():
        if not config[k]:
            empty_keys.append(k)

    if len(empty_keys) > 0:
        res["is_config_file"] = True
        res["empty_keys"] = empty_keys

        return res

    else:
        res["is_config_file"] = True
        res["data"] = config

        return res


def extract_dates_from_string(string: str) -> list:
    if ("from" in string) and ("to" in string):
        date_time_list = []
        dates = string.split("from")[1].split("to")

        for date in dates:
            date_time = {"date": None, "time": None, "time_zone": None}

            if (",") in date:
                date_part = date.split(",")[0]
                time_part = date.split(",")[1]
                if ("+" in time_part) or ("-" in time_part):
                    time_part_split = []
                    if "+" in time_part:
                        time_part_split = time_part.split("+")
                        time_part_split[1] = "+" + time_part_split[1]
                        date_time["time"] = time_part_split[0]
                        date_time["time_zone"] = time_part_split[1]

                    if "-" in time_part:
                        time_part_split = time_part.split("-")
                        time_part_split[1] = "-" + time_part_split[1]
                        date_time["time"] = time_part_split[0]
                        date_time["time_zone"] = time_part_split[1]

                else:
                    date_time["date"] = date_part
                    date_time["time"] = time_part

                date_time["date"] = date_part
                date_time_list.append(date_time)

            else:
                date_time["date"] = date
                date_time_list.append(date_time)

        return date_time_list

    elif "on" in string:
        date_time_list = []
        date = string.split("on")[1]
        date_time = {"date": None, "time": None, "time_zone": None}

        if (",") in date:
            date_part = date.split(",")[0]
            time_part = date.split(",")[1]
            if ("+" in time_part) or ("-" in time_part):
                time_part_split = []
                if "+" in time_part:
                    time_part_split = time_part.split("+")
                    time_part_split[1] = "+" + time_part_split[1]
                    date_time["time"] = time_part_split[0]
                    date_time["time_zone"] = time_part_split[1]

                if "-" in time_part:
                    time_part_split = time_part.split("-")
                    time_part_split[1] = "-" + time_part_split[1]
                    date_time["time"] = time_part_split[0]
                    date_time["time_zone"] = time_part_split[1]

            else:
                date_time["date"] = date_part
                date_time["time"] = time_part

            date_time["date"] = date_part
            date_time_list.append(date_time)

            return date_time_list
        else:
            date_time["date"] = date
            date_time_list.append(date_time)

            return date_time_list
    else:
        raise ValueError("Invalid date value.")


def get_config_command(string: str) -> dict:
    if find_keyword("help")(string):
        return {"name": "help", "args": None}

    elif find_keyword("get")(string):
        return {"name": "get", "args": None}

    elif find_keyword("delete")(string):
        arg_value_pair = "".join(string.split()).split("--")[1:]

        if len(arg_value_pair) == 0:
            raise ValueError("Invalid argument.")

        separated_pair = arg_value_pair[0].split("=")

        if (find_keyword("channel_ping_words")(separated_pair[0])) or (
            find_keyword("consult_agent_ids")(separated_pair[0])
        ):
            if "," in separated_pair[1]:
                return {
                    "name": "delete",
                    "args": {separated_pair[0]: separated_pair[1].split(",")},
                }

            else:
                return {
                    "name": "delete",
                    "args": {separated_pair[0]: [separated_pair[1]]},
                }

        else:
            raise ValueError("Invalid argument.")

    elif find_keyword("set")(string):
        arg_value_pair = "".join(string.split()).split("--")[1:]

        if len(arg_value_pair) == 0:
            raise ValueError("Invalid argument.")

        args = {
            "channel_ping_words": [],
            "consult_agent_ids": [],
            "reaction_for_handling": None,
            "reaction_for_invalid": None,
            "reaction_for_no_research": None,
        }

        for pair in arg_value_pair:
            separated_pair = pair.split("=")

            if (len(separated_pair) <= 1) or ("" in separated_pair):
                raise ValueError("Invalid argument.")

            if (
                (find_keyword("channel_ping_words")(separated_pair[0]))
                or (find_keyword("consult_agent_ids")(separated_pair[0]))
                or (find_keyword("reaction_for_handling")(separated_pair[0]))
                or (find_keyword("reaction_for_invalid")(separated_pair[0]))
                or (find_keyword("reaction_for_no_research")(separated_pair[0]))
            ):
                args[separated_pair[0]] = separated_pair[1]

                if separated_pair[0] == "channel_ping_words":
                    if "," in separated_pair[1]:
                        args["channel_ping_words"] = separated_pair[1].split(",")
                    else:
                        args["channel_ping_words"] = [separated_pair[1]]

                if separated_pair[0] == "consult_agent_ids":
                    if "," in separated_pair[1]:
                        args["consult_agent_ids"] = separated_pair[1].split(",")
                    else:
                        args["consult_agent_ids"] = [separated_pair[1]]
            else:
                raise ValueError("Invalid argument.")

        for k, v in args.items():
            if k not in (
                "channel_ping_words",
                "consult_agent_ids",
                "reaction_for_handling",
                "reaction_for_invalid",
                "reaction_for_no_research",
            ):
                raise ValueError("Invalid argument.")

        return {"name": "set", "args": args}

    else:
        raise ValueError("Invalid command.")


def get_consult_command(string: str) -> dict:
    if find_keyword("formats")(string):
        return {"name": "formats"}

    elif find_keyword("all")(string):
        s = "".join(string.split())
        split = s.split("all")

        return {"name": "all", "args": {"date_time": split[1]}}

    elif find_keyword("handled")(string):
        s = "".join(string.split())
        split = s.split("handled")

        return {"name": "handled", "args": {"date_time": split[1]}}

    elif find_keyword("unhandled")(string):
        s = "".join(string.split())
        split = s.split("unhandled")

        return {"name": "unhandled", "args": {"date_time": split[1]}}

    elif find_keyword("with-ping-word")(string):
        s = "".join(string.split())
        split = s.split("with-ping-word")

        return {"name": "with_ping_word", "args": {"date_time": split[1]}}

    else:
        raise ValueError("Invalid command.")
