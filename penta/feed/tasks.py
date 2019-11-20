# -*- coding: utf-8 -*-

import sys
import json
import codecs
import logging
import requests
import urllib.parse
import isodate

from selenium import webdriver
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from his.penta.curator.models import CuratorUserWatched, CuratorPlaylist, \
    CuratorViews, SuggestPlaylistFromQuestion, CuratorChannel, CuratorLink
from his.penta.feed.models import FacebookUser

logger = logging.getLogger(__name__)


@shared_task
def create_page_snapshot(host, quoted_norm_path, snapshot_path):
    print("INIT {0}".format(quoted_norm_path))
    try:
        url = u'http://{0}{1}?no_analytic=true'.format(host, quoted_norm_path )
        browser = webdriver.PhantomJS()
        browser.set_window_size(1024, 768)
        browser.set_page_load_timeout(15) 
        browser.get(url)
        html = browser.page_source.replace('<meta name="fragment" content="!">', '')
        browser.close()
        browser.quit()
        f = codecs.open(snapshot_path, 'wt', 'utf-8')
        f.write(html)
        f.close()
    except Exception as e:
        print(e)


@shared_task
def save_view_stat(playlist_id, user_id):
    playitem = CuratorPlaylist.objects.filter(id=playlist_id).first()
    if playitem:
        with transaction.atomic():
            CuratorUserWatched.objects.log(playlist_id, user_id)
            CuratorViews.objects.create_views("playlist", playitem)
            CuratorViews.objects.create_views("channel", playitem.channel)
            (SuggestPlaylistFromQuestion.objects
             .filter(questionthread__created_by_id=user_id,
                     playlist_id=playlist_id, first_watch=None)
             .update(first_watch=timezone.now()))


def fetch_feed_facebook(userID, accessToken, edge):
    data_all = []
    facebookUser = FacebookUser.objects.filter(facebook_user_id=userID)
    latest_query_time = None
    if facebookUser.count() > 0:
        latest_query_time = facebookUser[0].latest_query_time

    try:
        data = {'method': 'GET', 'format': 'json', 'suppress_http_code': '1', 'access_token': accessToken}
        body = urllib.parse.urlencode(data)
        url = 'https://graph.facebook.com/' + userID + '/' + edge + '?' + body
        r = requests.get(url)
        content = r.content
        content = json.loads(content)

        for content_data in content['data']:
            if content_data['type'] == 'video':
                data_all.append(content_data)

        # print 'fetch data from ' + url

        foundOldFeed = False
        while 'paging' in content:

            if 'next' in content['paging']:
                url = content['paging']['next'] + '&' + body
            else:
                break

            r = requests.get(url)
            content = r.content
            content = json.loads(content)
            # print 'fetch next data from ' + url

            for content_data in content['data']:

                if content_data['type'] != 'video' or 'link' not in content_data:
                    continue

                content_time = isodate.parse_datetime(content_data['updated_time'])
                if latest_query_time is None or latest_query_time < content_time:
                    data_all.append(content_data)
                else:
                    logger.debug('latest query time[%s] > %s, cancel next query.',
                                 str(latest_query_time), content_data['updated_time'])
                    foundOldFeed = True
                    break

            if foundOldFeed:
                break

        # print 'data size ' + str(len(data_all))
        return data_all
    except Exception as e:
        logger.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        logger.error('Error %s' % e)
        return data_all


def get_feed_facebook(userID, accessToken, edge):
    try:
        videos = []
        data_all = fetch_feed_facebook(userID, accessToken, edge)

        for data in data_all:
            playlistLink = []
            video_type = ''
            # print '======================================+'
            # pprint(data.get('format'))
            # print data['type']
            # print data.get('link')
            # print data.get('is_expired')
            # print '======================================+'
            if 'link' in data:
                if 'youtube' in data['link'] or 'youtu.be' in data['link']:
                    video_type = 'Y'
                elif 'dailymotion' in data['link']:
                    video_type = 'D'
                elif 'facebook' in data['link']:
                    video_type = 'F'
                else:
                    video_type = 'E'  # ignore unsupported videos
                    continue
            else:
                video_type = 'E'  # ignore unsupported videos
                continue

            video_id = ''
            parsed = urllib.parse.urlparse(data['link'])
            # print parsed.path
            if video_type == 'Y':
                if '//youtu.be' in data['link']:
                    video_id = parsed.path[1:]
                elif '//www.youtube.com/embed/' in data['link'] or '//www.youtube.com/embed/' in data['link']:
                    video_id = parsed.path[len('/embed/'):]
                else:
                    video_id = urllib.parse.parse_qs(parsed.query)['v'][0]
            elif video_type == 'F':
                # print parsed.path
                # print data['link']
                # print '==================-------------=============='
                if '/videos/' in parsed.path:
                    path = parsed.path.split('/')
                    found_video = False
                    for n in path:
                        if found_video:
                            video_id = n
                            break
                        elif n == "videos":
                            found_video = True
                elif 'v' in urllib.parse.parse_qs(parsed.query):
                    video_id = urllib.parse.parse_qs(parsed.query).get('v')

            elif video_type == 'D':
                if '/video/' in parsed.path:
                    video_id = parsed.path[len('/video/'):]
                else:
                    video_id = ''
            else:
                video_id = ''
            logger.debug('%s  =>  %s', data['link'], video_id)

            if 'name' in data:
                name = data['name']
            elif 'message' in data:
                name = data['message']
            else:
                name = data['link']

            thumbnail_video = data['picture']
            if isinstance(video_id, list):
                video_id = video_id[0]
            if video_type == 'Y':
                thumbnail_video = 'http://img.youtube.com/vi/' + video_id + '/hqdefault.jpg'
            elif video_type == 'D':
                thumbnail_video = 'http://www.dailymotion.com/thumbnail/video/' + video_id

            playlistLink.append(
                {'name': name, 'thumbnail': thumbnail_video, 'video_id': video_id, 'video_type': video_type})
            owner = []
            owner_url = 'https://www.facebook.com/' + data['from']['id']
            owner_img = 'http://graph.facebook.com/' + data['from']['id'] + '/picture?width=240&height=240'
            owner.append({'name': data['from']['name'], 'img': owner_img, 'url': ''})
            updated_time_str = data['updated_time']
            updated_time = isodate.parse_datetime(updated_time_str)
            updated_time = updated_time.replace(tzinfo=None)
            video = {
                'id': 'facebook_' + data['id'],
                'feed_id': data['id'],
                'name': name,
                'owner': owner,
                'favorite': [],
                'timestamp': timezone.now() - updated_time,
                'time': updated_time,
                'thumbnail': playlistLink[0],
                'playlist': playlistLink
            }
            videos.append(video)

        return videos
    except Exception as e:
        logger.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        logger.error('Error %s' % e)
        return []


@transaction.atomic
def save_feed_facebook(videos, curatorChannel, user):
    playlist = CuratorPlaylist.objects.filter(channel=curatorChannel)
    # from pprint import pprint
    # pprint(videos)
    for video in videos:
        video_id = video['playlist'][0]['video_id']
        video_type = video['playlist'][0]['video_type']
        exist = playlist.filter(link__video_id=video_id, link__video_type=video_type)
        if not exist:
            if video_type == 'F':
                url = 'https://www.facebook.com/video/embed?video_id=%s' % video['playlist'][0]['video_id']
            elif video_type == 'Y':
                url = 'https://www.youtube.com/watch?v=%s' % video['playlist'][0]['video_id']
            elif video_type == 'D':
                continue  # not support dailymotion until found valid url
            try:
                link = CuratorLink.objects.get_video_link(url)
                link.create_new_playlist(curatorChannel)
            except Exception as e:
                logger.error(e)


@shared_task
def utils_get_feed_facebook(userID, accessToken, user):
    """
    /me/posts
        - api returns the posts created by the user (on her own wall or the wall of a friend),
        and it may include any kind of content such as shared links, checkins, photos and status updates.
    /me/feed
        - includes all the things that a user might see on his own wall;
        again shared links, checkins, photos and status updates. This also includes posts made by friends on the user's wall.
    /me/statuses
        - api returns only status updates posted by the user on his own wall.
    /me/home
        - api returns a stream of all the posts created by you and your friends,
        i.e. what you usually find on the “News Feed” of Facebook.
    """
    feed_videos = get_feed_facebook(userID, accessToken, 'feed')
    home_videos = get_feed_facebook(userID, accessToken, 'home')

    all_video = []

    tmp = feed_videos + home_videos
    for video in tmp:
        duplicate = False
        for video2 in all_video:
            if video['id'] == video2['id']:
                duplicate = True
                break
        if not duplicate:
            all_video.append(video)

    logger.debug(all_video)
    logger.debug('completed get feed facebook. result : %d', len(all_video))

    facebookUser, created = FacebookUser.objects.get_or_create(facebook_user_id=userID)
    facebookUser.latest_query_time = timezone.now()
    facebookUser.save()
    logger.debug('save new last query time')

    curatorChannel, isChannelCreated = CuratorChannel.objects.get_or_create(user=user, name='Facebook')
    if isChannelCreated:
        logger.debug( 'Facebook channel not found, create new channel.')
        curatorChannel.name = 'Facebook'
        curatorChannel.detail = 'Auto generate channel.'
        curatorChannel.icon_url = settings.MEDIA_URL + 'images/facebook_512.png'
        curatorChannel.save()

    save_feed_facebook(all_video, curatorChannel, user)
