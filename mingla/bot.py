import random
import uuid
import time
import re
from datetime import datetime
from slack import WebClient
from slack.errors import SlackApiError


def n_even_chunks(lst, n):
    """Yield n as even chunks as possible from lst."""
    last = 0
    for i in range(1, n + 1):
        cur = int(round(i * (len(lst) / n)))
        yield lst[last:cur]
        last = cur


class Bot:
    def __init__(self, token, config, bot_env):
        self.client = None
        self.token = token
        self.config = config
        self.bot_env = bot_env

    def init_slack(self):
        self.client = WebClient(self.token)

    def get_subjects(self):
        subjects = self.config["subjects"]
        return f"*{random.choice(subjects)}* eller *{random.choice(subjects)}*"

    def get_place(self):
        places = self.config["places"]
        return random.choice(places)

    def get_tips(self):
        tips = self.config["tips"]
        return random.choice(tips)

    def invite_members_to_room(self, list_of_reaction_members):
        random.shuffle(list_of_reaction_members)
        attach = []

        if len(list_of_reaction_members) < self.config["group_size"]:
            text = self.config["texts"]["noop"]
        else:
            text = self.config["texts"]["intro"]

        for chunk in n_even_chunks(
            list_of_reaction_members,
            len(list_of_reaction_members) // self.config["group_size"],
        ):
            users = ", ".join([f"<@{x}>" for x in chunk])
            attach.append(
                {
                    "fallback": "TODO",
                    "color": "#36a64f",
                    "title": f"{self.get_place()}",
                    "title_link": f"https://meet.jit.si/ur-mingla-{uuid.uuid4().hex}",
                    "text": f"Förslag på ämnen är {self.get_subjects()}",
                    "footer": f"{users}",
                }
            )

        if len(list_of_reaction_members) >= self.config["group_size"]:
            attach.append(
                {
                    "fallback": "TODO",
                    "color": "#9803fc",
                    "title": "Information om hur botten funkar",
                    # TODO: change below to UR related git repo
                    "title_link": "https://git.svt.se/stbe02/mingla/-/blob/master/README.md",
                    "text": self.config["texts"]["footer"],
                    "footer": f"Dagens tips: {self.get_tips()}",
                }
            )

        try:
            self.client.chat_postMessage(
                username="mingla",
                channel=self.config["environments"][self.bot_env]["channel"],
                icon_emoji=":coffee:",
                text=text,
                attachments=attach,
            )
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]
            print(f"Got an error: {e.response['error']}")

    def add_reaction(self, message, reaction):
        self.client.reactions_add(
            channel=self.config["environments"][self.bot_env]["channel"],
            timestamp=message["ts"],
            name=reaction,
        )

    def remove_reaction(self, message, reaction):
        self.client.reactions_remove(
            channel=self.config["environments"][self.bot_env]["channel"],
            timestamp=message["ts"],
            name=reaction,
        )

    def get_reactions(self, message):
        message = self.client.reactions_get(
            channel=self.config["environments"][self.bot_env]["channel"],
            timestamp=message["ts"],
        )
        return message["message"].get("reactions", [])

    def get_reaction(self, message, reaction):
        for r in self.get_reactions(message):
            if r["name"] == reaction:
                return r

    def get_users_reaction(self, message, reaction):
        r = self.get_reaction(message, reaction)
        if r:
            return r["users"]
        return []

    def find_daily_reaction_message(self):
        response = self.client.conversations_history(
            channel=self.config["environments"][self.bot_env]["channel"]
        )
        for message in response["messages"]:
            yday = datetime.now().timetuple().tm_yday
            if (
                message.get("user") == self.config["bot_id"]
                and re.match(fr"^VOTE {yday}.*", message["text"]) is not None
            ):
                return message

    def list_active_users_in_room(self):
        if self.bot_env == "production":
            list_of_online_members = []
        else:
            # use your own userid for development
            list_of_online_members = ["U06LM2VJ8"] * int(random.random() * 10)

        response = self.client.conversations_members(
            channel=self.config["environments"][self.bot_env]["channel"]
        )
        if response.get("ok"):
            for member in response.get("members", []):
                r = self.client.users_getPresence(user=member)
                if r.get("ok") and r.get("presence") == "active":
                    list_of_online_members.append(member)
        return list_of_online_members

    def send_message(self, text):
        try:
            response = self.client.chat_postMessage(
                username="mingla",
                channel=self.config["environments"][self.bot_env]["channel"],
                icon_emoji=":coffee:",
                text=text,
            )
            return response
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]
            print(f"Got an error: {e.response['error']}")
