from django.db import models
from django.db.models import Sum

from bot.settings import CATEGORIES, NAMES


class Entry(models.Model):
    CATEGORIES_CHOICES = ((category, category) for category in CATEGORIES)
    category = models.CharField(max_length=16,
                                choices=CATEGORIES_CHOICES)

    NAMES_CHOICES = ((name, name) for name in NAMES)

    person = models.CharField(max_length=5, choices=NAMES_CHOICES)

    date = models.DateField(auto_now=True)
    description = models.TextField(default="")
    bourgeois = models.BooleanField(default=False)
    cost = models.IntegerField(default=0)

    def __str__(self):
        return "Сохранено: категория {category}, сумма {cost}, описание {description}, буржуйство {bourgeois}, кто {person}".format(
            category=self.category, cost=self.cost, description=self.description, bourgeois=self.bourgeois, person=self.person)

    @staticmethod
    def _get_statistics(query_set, fields=['category', 'person']):
        """Return string with costs statistics by given fields

        List sums by possible values of given fields

        Parameters
        ----------
        query_set : django.db.models.query.QuerySet
            Entries to consider

        Returns
        -------
        str
            Describes sum stats for entries in query_set
        """

        field_values = {field: [{'database': choice[0], 'displayed': choice[1]}
                                for choice in Entry._meta.get_field(field).choices] for field in fields}

        msg = ""

        for field in fields:

            costs = [(field_value['displayed'], query_set.filter(**{field: field_value['database']}).aggregate(cost_sum=Sum('cost')))
                     for field_value in field_values[field]]
            costs_text = "\n".join([item[0] + ': ' + str(item[1]['cost_sum'])
                                   for item in costs]) + "\n\n"
            msg += costs_text

        return msg

    @staticmethod
    def get_statistics(query_set):
        """Return string with costs statistics

        List sums by category and person (with 'bourgeois' flag)

        Parameters
        ----------
        query_set : django.db.models.query.QuerySet
            Entries to consider

        Returns
        -------
        str
            Describes sum stats for entries in query_set
        """

        cost = query_set.aggregate(cost_sum=Sum('cost'))
        msg = "общая сумма: {cost}\n\n".format(cost=cost['cost_sum'])

        msg += Entry._get_statistics(query_set)

        bourgeois = query_set.filter(bourgeois=True)
        bourgeois_cost = bourgeois.aggregate(cost_sum=Sum('cost'))
        msg += "буржуйство: {cost}\n\n".format(cost=bourgeois_cost['cost_sum'])

        msg += Entry._get_statistics(bourgeois, fields=['person'])

        return msg
