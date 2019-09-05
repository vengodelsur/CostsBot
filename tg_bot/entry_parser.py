import re

from costs.models import Entry

from bot.settings import CATEGORIES


class EntryParser:
    CATEGORIES_PATTERN = '(' + '|'.join(CATEGORIES) + ')'
    COST_PATTERN = '\d+'
    BOURGEOIS_PATTERN = '(буржуйство)'

    categories_group = '(?P<category>{pattern})'.format(
        pattern=CATEGORIES_PATTERN)
    cost_group = '(?P<cost>{pattern})'.format(pattern=COST_PATTERN)
    bourgeois_group = '(?P<bourgeois>{pattern})'.format(
        pattern=BOURGEOIS_PATTERN)
    description_group = '(?P<description>((?=.*\S.*)((?!{other_slots}).)*))'.format(
        other_slots='|'.join([BOURGEOIS_PATTERN, CATEGORIES_PATTERN, COST_PATTERN]))

    slot_re = '((' + '|'.join(
        [categories_group, cost_group, bourgeois_group, description_group]) + ')(\s|$))'
    ENTRY_RE = re.compile(slot_re + '+')

    def parse(self, text):
        """Try to parse text as costs entry

        The result is stored as match attribute.

        Parameters
        ----------
        text : str
            User input to be parsed.

        Returns
        -------
        bool
            True if successful (matches found), False otherwise (no match can be found).

        Examples
        --------
        >>> self.parse("еда 300 обед")
        True

        >>> self.parse("    ")
        False

        """

        self.match = re.match(self.ENTRY_RE, text)
        return (self.match is not None)

    def get_entry(self, name):
        """Return Entry instance created from found matches (saved in database)

        Parameters
        ----------
        name : str
            Name of Telegram user to be stored in entry.

        Returns
        -------
        Entry
            None if entry can't be saved (missing or incorrect values in match)


        """
        try:
            entry = Entry(category=self.match.group('category'), description=self.match.group(
                'description'), cost=int(self.match.group('cost')), bourgeois=(self.match.group('bourgeois') is not None), person=name)
            entry.save()
            return entry
        except:
            return None

    def get_parsed(self):
        """Return text description of found matches


        Returns
        -------
        str
            Text description of found matches (stored as 'match' attribute).

        """
        return "категория {category}, сумма {cost}, описание {description}, буржуйство {bourgeois}".format(
            category=self.match.group('category'), cost=self.match.group('cost'), description=self.match.group('description'), bourgeois=self.match.group('bourgeois'))
