from __future__ import print_function, unicode_literals, division

from django.template.loader import get_template
from future.builtins import int

import os
import re
import gzip
import pytz
import logging

from dateutil import parser
from celery.task import task
from django.utils import timezone
from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.core.mail import EmailMessage, EmailMultiAlternatives
from six import StringIO

from his.penta.apis.youtube import get_youtube_video_info
from his.penta.curator.models import CuratorPlaylist, CuratorLink

try:
    logger = logging.getLogger(__name__)
except Exception as e:
    logger = logging.getLogger()


@task
def summary_weekly_basic_track():
    """
    track latest week video view
    """
    # Parse Log
    last_log = None
    gzip_logs = []
    pattern = re.compile(r'^\S* (?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) '
                         r'views (?P<username>\S+) (?P<type>\S+) (?P<vid>\S+) '
                         r'(?P<action>\S+) (?P<current>\d+) (?P<client>\S+).*$')
    parsed_log = []

    now = timezone.now()
    last_week = now - timezone.timedelta(days=7)

    for root, dirs, files in os.walk('/var/log/pentachannel_persistent/'):
        for f in files:
            if f.startswith('vid_player_track.log'):
                if f.endswith('.gz'):
                    d = f.split('.')[1].split('-')[1]
                    d = parser.parse(d)
                    gzip_logs.append((d, os.path.join(root, f)))
                else:
                    last_log = (now, os.path.join(root, f))
    gzip_logs = sorted(gzip_logs)
    logs = gzip_logs + [last_log]
    logger.debug('Log files:')
    logger.debug(logs)
    for d, log in logs:
        if d.date() < last_week.date():
            continue
        if log.endswith('.gz'):
            f = gzip.open(log)
        else:
            f = open(log, 'r')
        for line in f:
            tmp = pattern.match(line)
            if not tmp:
                logger.warn('Line is not match')
                logger.warn('file: %s', log)
                logger.warn(line)
                continue
            try:
                dt = parser.parse(tmp.group('dt'))
                dt = pytz.utc.localize(dt)
                if dt < last_week:
                    continue
                data = {
                    'datetime': dt,
                    'username': tmp.group('username'),
                    'type': tmp.group('type'),
                    'vid': tmp.group('vid'),
                    'action': tmp.group('action'),
                    'current': int(tmp.group('current')),
                    'client': tmp.group('client') if tmp.group('client') != 'None' else None
                }
                parsed_log.append(data)
            except (TypeError, ValueError) as e:
                logger.warn('Cannot parse a line in file: %s', log)
                logger.warn(line)
                logger.warn(e.message, exc_info=1)
        f.close()

    # Analyze
    playlist_data = {}
    link_data = {}
    youtube_data = {}

    for data in parsed_log:
        if data['type'] == 'playlist':
            data_set = playlist_data
            use_int = True
        elif data['type'] == 'link':
            data_set = link_data
            use_int = True
        elif data['type'] == 'youtube':
            data_set = youtube_data
            use_int = False
        else:
            continue
        vid = int(data['vid']) if use_int else data['vid']
        if vid not in data_set:
            data_set[vid] = set()
        data_set[vid].add(data['username'])

    playlist_name = {}
    link_name = {}

    playlists = (CuratorPlaylist.objects.filter(id__in=playlist_data.keys())
                 .values('id', 'name'))
    for p in playlists:
        playlist_name[p['id']] = p['name']

    links = (CuratorLink.objects.filter(id__in=link_data.keys())
             .values('id', 'name'))
    for l in links:
        link_name[l['id']] = l['name']

    youtube_info = get_youtube_video_info(youtube_data.keys())
    """
    info {dict}
    key: {
      ...,
      'snippet': {
        'title': '<title>'
      }
    }
    """
    stat = []
    for key, users in playlist_data.items():
        stat.append((playlist_name.get(key, 'deleted'), len(users), 'PentaCenter'))
    for key, users in link_data.items():
        stat.append((link_name.get(key, 'deleted'), len(users), 'PentaCenter'))
    for key, users in youtube_data.items():
        snippet = youtube_info.get(key, {}).get('snippet', None)
        title = snippet['title'] if snippet else 'not found'
        stat.append((title, len(users), 'YouTube'))

    stat = sorted(stat, key=lambda x: x[1], reverse=True)

    report = []
    for i, s in enumerate(stat):
        if i >= 100:
            break
        report.append({
            'name': s[0],
            'view': s[1],
            'source': 'Y' if s[2] == 'YouTube' else 'P',
        })

    html_template = get_template('videos_tagging/emails/top_100_inline.html')
    html_body = html_template.render({'stat': report})

    bare_template = get_template('videos_tagging/emails/top_100_bare.html')
    bare_body = bare_template.render({'stat': report})

    full_report = NamedTemporaryFile('w', suffix='.csv', prefix='penta-top-100')
    for s in stat:
        full_report.write((u"\"%s\",%d,%s\n" % (s[0].replace('"', r'\"'), s[1], s[2])).encode('utf8'))
    full_report.flush()
    email = EmailMultiAlternatives(subject='Penta TOP 100',
                                   body=bare_body,
                                   from_email='showtime@penta.center',
                                   to=settings.ADMIN_EMAILS)
    email.attach_alternative(html_body, "text/html")
    email.attach_file(full_report.name)
    email.send()
    full_report.close()


if __name__ == '__main__':
    summary_weekly_basic_track()
