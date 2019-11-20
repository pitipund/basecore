from django.db import models


class Replace(models.Func):
    function = 'REPLACE'

    def __init__(self, expression, from_text, to_text, **extra):
        """
        expression: Replace all occurrences in string of substring from with substring to
        """
        if not hasattr(from_text, 'resolve_expression'):
            from_text = models.Value(from_text)
        if not hasattr(to_text, 'resolve_expression'):
            to_text = models.Value(to_text)

        expressions = [expression, from_text, to_text]
        super(Replace, self).__init__(*expressions, **extra)
