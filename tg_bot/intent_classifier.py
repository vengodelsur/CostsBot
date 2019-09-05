class IntentClassifier:

    def __init__(self, commands_list, entry_parser):
        self.commands_list = commands_list
        self.entry_parser = entry_parser

    def predict(self, text):
        """Return string describing user intent

        If user input doesn't equal any of commands in self.commands_list, try to parse it as costs entry.

        Parameters
        ----------
        text : str
            User input

        Returns
        -------
        str
            Describes user intent
        """

        if text in self.commands_list:
            intent = text

        else:
            parsed = self.entry_parser.parse(text)
            if parsed:
                intent = 'add_entry'

            else:
                intent = 'unknown'
        return intent
