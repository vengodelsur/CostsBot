import json
import requests
import datetime
from functools import wraps

from django.http import JsonResponse
from django.views import View

from costs.models import Entry
from .entry_parser import EntryParser
from .intent_classifier import IntentClassifier

TELEGRAM_URL = "https://api.telegram.org/bot"


from bot.settings import CATEGORIES, USERNAMES, BOT_TOKEN, ADMIN_USERNAME

COMMANDS = ["help", "stats"]

ADMIN_MESSAGE = '\n\nПо всем вопросам обращайтесь к админу {username}'.format(
    username=ADMIN_USERNAME)

ADD_ENTRY_HOW_TO = "Чтобы добавить покупку, введите в любом порядке через пробел: категорию, сумму (целое число), описание (не должно содержать названий категорий и чисел), например:\n\"300 сытный обед еда\"\n\nКатегории:\n{categories}".format(
    categories="\n".join(CATEGORIES))

COMMANDS_HELP = "/help : помощь\n/stats: статистика расходов за месяц"

HELP_MESSAGE = COMMANDS_HELP + "\n" + ADD_ENTRY_HOW_TO + ADMIN_MESSAGE

UNKNOWN_MESSAGE = "Неизвестная команда\n\n" + HELP_MESSAGE


class BotView(View):
    commands_list = COMMANDS
    entry_parser = EntryParser()
    intent_classifier = IntentClassifier(commands_list, entry_parser)

    def __init__(self):
        super().__init__()
        self.intent_handlers = {
            'help': self.handle_help, 'stats': self.handle_stats,
                               'add_entry': self.handle_add_entry, 'unknown': self.handle_unknown}

    def post(self, request, *args, **kwargs):

        t_data = json.loads(request.body)
        t_message = t_data["message"]
        self.chat_id = t_message["chat"]["id"]
        self.name = USERNAMES[t_message["from"]["username"]]

        try:
            text = t_message["text"].strip().lower()
        except Exception as e:
            return JsonResponse({"ok": "POST request processed"})

        text = text.lstrip("/")

        intent = self.intent_classifier.predict(text)
        self.intent_handlers[intent]()

        return JsonResponse({"ok": "POST request processed"})

    def send_message(self):
        data = {
            "chat_id": self.chat_id,
            "text": self.message.encode('utf-8'),
            "parse_mode": "Markdown",
        }
        response = requests.post(
            f"{TELEGRAM_URL}{BOT_TOKEN}/sendMessage", data=data
        )

    def message_sender(func):
        """Add message sending behaviour to function (used for intent handlers).
        """
        @wraps(func)
        def wrapper(self):
            func(self)
            self.send_message()
        return wrapper

    @message_sender
    def handle_unknown(self):
        """Handle unknown commands.

        Set 'message' attribute to message for unknown commands.
        """
        self.message = UNKNOWN_MESSAGE

    @message_sender
    def handle_stats(self):
        """Handle /stats command.

        Set 'message' attribute to string with entry statistics for this month (costs sum by person and by category).
        """

        today = datetime.date.today()
        entries = Entry.objects.filter(date__month=today.month)
        self.message = Entry.get_statistics(entries)

    @message_sender
    def handle_help(self):
        """Handle /stats command.

        Set 'message' attribute to help message (listing commands and entry categories).
        """
        self.message = HELP_MESSAGE

    @message_sender
    def handle_add_entry(self):
        """Try to add entry.

        If succesful, set 'message' attribute to text description of saved entry, otherwise notify the user and give description of how the input was parsed
        """
        entry = self.entry_parser.get_entry(self.name)
        if (entry):
            self.message = str(entry)
        else:
            self.message = "Не могу сохранить покупку: " + \
                self.entry_parser.get_parsed() + " кто {person}".format(
                    person=self.name) + ADMIN_MESSAGE
