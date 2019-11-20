import re
import math
import traceback
from django.db import models, transaction

from his.penta.curator.models import CuratorTag, CuratorPlaylist


class TagDecision(models.Model):
    target_tag = models.OneToOneField(CuratorTag, related_name='tag_decision')
    exec_function = models.TextField(null=False, blank=True, default='',
                                     help_text='python code can access feature check '
                                               'results with `args[x]` and must set '
                                               'variable `result` before code ended.'
                                               '`result` must be boolean.')
    enabled = models.BooleanField(default=True)

    def execute(self, playlist):
        """
        Check the input playlist whether it should be tagged with target_tag
        or not. Before this function execute `exec_function` it with generate
        feature results store in dict  `args[x]`  which  `x`  is an order of
        TagFeature. Before the end of  `exec_function`  you must set the
        `result`  variable to  `True`  if you want to tag the playlist with
        target_tag,  `False`  otherwise.

        In `exec_function`, module `math` and `re` have already been imported
        but you cannot `import` other modules
        """
        result = None
        error = None
        args = {}
        for feature in self.features.all():
            args[feature.order] = feature.check_feature(playlist)
        try:
            if (re.search('^import .*$', self.exec_function) or
                    re.search('^form .* import .*$', self.exec_function)):
                raise AssertionError('You cannot use `import` in exec_function.')
            exec(self.exec_function)
            if result is None:
                error = 'No result'
        except Exception:
            error = traceback.format_exc()
        return result, error

    @classmethod
    def help_text(cls):
        return cls.execute.__doc__ + """
        # Example
        
        Given three TagFeature with order 0, 1, and 2,
        which feature no. 0 and 1 are boolean and feature no. 2 is quantitative 
        and exec_function exact below.
        
        ```
        result = False
        if args[0]:
            if not args[1]:
                result = True
            elif args[2] > 0.5:
                result = True
        ```
        
        The playlist will be tagged if feature no. 0 is True and no. 1 is False
        or feature no. 0 is True and no. 2 is more than 0.5
        """

    def get_feature_count(self):
        return self.features.all().count()

    get_feature_count.short_description = 'feature count'

    def __unicode__(self):
        return 'TagDecision of <%s>' % self.target_tag.name

    def __str__(self):
        return 'TagDecision of <%s>' % self.target_tag.name


class TagFeature(models.Model):
    FEATURE_MATCH_TEXT = 'M'
    FEATURE_HAS_TAG = 'T'
    _FEATURE_TYPE_CHOICES = (
        (FEATURE_MATCH_TEXT, 'matched text'),
        (FEATURE_HAS_TAG, 'has tag'),
    )

    tag_decision = models.ForeignKey(TagDecision, related_name='features')
    feature_type = models.CharField(max_length=1, choices=_FEATURE_TYPE_CHOICES)
    argument = models.TextField(null=False, blank=True, default='')
    order = models.IntegerField(null=False, blank=True)

    def check_feature(self, playlist):
        if not isinstance(playlist, CuratorPlaylist):
            raise ValueError('Input must be playlist')

        if self.feature_type == self.FEATURE_MATCH_TEXT:
            return self.match_text(playlist)
        elif self.feature_type == self.FEATURE_HAS_TAG:
            return self.has_tag(playlist)
        raise ValueError('unknown feature function')

    def help_text(self, feature_type=None):
        if not feature_type:
            feature_type = self.feature_type

        if feature_type == self.FEATURE_MATCH_TEXT:
            return self.match_text.__doc__
        elif feature_type == self.FEATURE_HAS_TAG:
            return self.has_tag.__doc__
        return None

    def match_text(self, playlist):
        """
        True if playlist name contained one or more word from argument.
        Argument must contain one or more words separated by ','.
        * Not case sensitive but whitespace sensitive
        ** Can also use regex (regular expression) but the regex
           must not contains ','
        """
        name = playlist.name.lower()
        args = self.argument.split(',')
        for arg in args:
            if re.search(arg.strip().lower(), name):
                return True
        return False

    def has_tag(self, playlist):
        """
        `True` if playlist has one of its tag ids matched one of
        the tag ids in the argument.
        The argument must contain one or more tag ids separated by ','
        * Tag ids must be integers
        """
        tags = list(playlist.channel.tags.all().values_list('id', flat=True))
        print(tags)
        args = [long(x) for x in self.argument.split(',')]
        print(args)
        for arg in args:
            try:
                if tags.index(arg) >= 0:
                    return True
            except ValueError:
                pass
        return False

    @transaction.atomic
    def move_order_to(self, to):
        if not isinstance(to, int) or to < 0:
            raise ValueError('order must be non negative integer')
        if self.order < to:
            affected_orders = self.tag_decision.features.filter(order_gt=self.order, order__lte=to)
            last = -1
            for tag_decision in affected_orders:
                tag_decision.order -= 1
                tag_decision.save()
                if tag_decision.order > last:
                    last = tag_decision.order
            self.order = last+1
            self.save()
        elif self.order > to:
            affected_orders = self.tag_decision.features.filter(order__gte=to, order__lt=self.order)
            for tag_decision in affected_orders:
                tag_decision.order += 1
                tag_decision.save()
            self.order = to
            self.save()

    def save(self, *args, **kwargs):
        exist_orders = self.tag_decision.features.all()
        if self.id:
            exist_orders = exist_orders.exclude(id=self.id)
        exist_orders = list(exist_orders.order_by('order'))

        if self.order is None:
            if exist_orders:
                self.order = exist_orders[-1].order + 1
            else:
                self.order = 0
        super(TagFeature, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s %s' % (self.tag_decision.target_tag.name, self.get_feature_type_display())

    def __str__(self):
        return '%s %s' % (self.tag_decision.target_tag.name, self.get_feature_type_display())

    class Meta:
        ordering = ['tag_decision', 'order']
