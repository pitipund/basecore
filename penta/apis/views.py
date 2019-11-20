# -*- coding: utf-8 -*-

import traceback
import urllib.parse
import logging
import base64
import hashlib
import hmac
import json
import operator
import re
import isodate
import celery
import random

from PIL import Image
from django.core.files.base import File
from six import BytesIO
from itertools import chain, islice
from uuid import uuid4
from functools import reduce

from his.penta.apis.account_api import AccountAPI

from django.contrib.auth.decorators import permission_required
from rest_framework.parsers import MultiPartParser
from django.db import transaction
from django.db.models import F, Q, Min, Max
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import *  # noqa
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from his.users.models import User, APIToken, MobileDevice, ApplicationDefaultRole
from his.penta.apis.parsers import ImageUploadParser
from his.penta.channel.utils import render_json_response
from his.penta.curator.models import CuratorChannel, CuratorLink, UserHaveChannel
from his.penta.curator.models import CuratorPlaylist, CuratorPlaylistExtra
from his.penta.curator.models import UserProfile
from his.penta.curator.models import CuratorTag
from his.penta.curator.models import SearchHistory, CuratorUserWatched, CuratorUserUnwantedLink
from his.penta.curator.models import CuratorMirror, CuratorMirrorRule
from his.penta.curator.models import QuestionForum, QuestionThread, SuggestPlaylistFromQuestion
from his.penta.curator.serializers import CuratorPlaylistSerializer, CuratorChannelSerializerWithTag, \
    CuratorChannelSerializer, CuratorChannelFullTagSerializerWithTag, \
    CuratorChannelSummarySerializer, CuratorPlaylistLinkSerializer, CuratorTagSerializer
from his.penta.curator.permissions import IsChannelOwner, has_edit_channel_permission, SUPER_ADMIN_LIST
from his.penta.curator.permissions import IsChannelOwnerOrReadOnly, IsPlaylistOwnerOrReadOnly
from his.penta.feed.models import FeedEmail, FeedEmailImage, FeedEmailTemplate, CuratorSuggestedLink
from his.penta.feed.permissions import IsSuggestedChannelOwner
from his.penta.feed.serializers import FeedEmailSerializer, FeedEmailSummarySerializer, FeedEmailImageSerializer, \
    FeedEmailTemplateSerializer, FeedEmailFullDetailSerializer, CuratorSuggestedLinkSerializer, \
    CuratorChannelSuggestedLinkSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_extensions.cache.decorators import cache_response
from his.penta.apis.serializer import SearchResultSerializer
from his.penta.apis.serializer import youtube_video_to_queueitem
from his.penta.apis.models import SoopVideo
from django.core.cache import cache
from datetime import datetime, timedelta
from his.penta.apis.tasks import update_get_link_from_tag, get_new_video_from_auto
from his.penta.apis.utils import calculate_key_for_cache, cache_response_anonymous_only

from his.penta.showtime.utils import VideoType, AccessLevel, ACCESS_LEVEL_CHOICES
from his.penta.showtime.push import pusher
from django.conf import settings
from django.utils import timezone
from django.db.transaction import atomic
from .youtube import youtube
import his.penta.apis.youtube as my_youtube

logger = logging.getLogger(__name__)
S_KEY = b"ZXNXcx8/u+mGnbKokC0HRAdeVW6L5qGJTf4n18zJloAcBaBp9LyNED7wkvhihobWHLobBcAyfKORoWdzhTd5Cw=="


@csrf_exempt
def add_stream(request):
    data = json.loads(request.body)
    links = data['links']
    channel_id = int(data['channel'])
    # print data
    # print 'get channel with channel id ', channel_id
    channel = CuratorChannel.objects.get(id=channel_id)

    playlists = CuratorPlaylist.objects.filter(channel=channel)
    all_links = []
    for playlist in playlists:
        if playlist.link is not None:
            all_links.append(playlist.link)

    new_playlist = None
    for link in links:
        stream_info = {
            'name': link['name'],
            'video_id': link['video_id'],
            'thumbnail_url': link['thumbnail_url'],
            'duration': 0,
            'payload': link['payload']
        }
        curator_link = CuratorLink.objects.get_video_link(link['url'], stream_info)
        if curator_link in all_links:
            curator_link.video_id = link['video_id']
            curator_link.thumbnail_url = link['thumbnail_url']
            curator_link.payload = link['payload']
            curator_link.save()
        else:
            new_playlist = curator_link.create_new_playlist(channel)

    if new_playlist is not None:
        new_playlist.pin()

    return render_json_response({'success': True})


@permission_required(['is_staff', 'is_superuser'])
def api_docs(request):
    import urls
    data = []
    for url in urls.urlpatterns:
        data.append({
            'name': url.name,
            'pattern': url.regex.pattern,
            'doc': url.callback.func_doc,
        })
    context = {
        'urls': data
    }
    return render(request, 'api/docs.html', context)


@csrf_exempt
@atomic
def add_video(request):
    data = json.loads(request.body)
    videos = data['videos']
    channel_id = int(data['channelId'])
    channel = CuratorChannel.objects.get(id=channel_id)
    new_playlist = None
    for video in videos:
        if video['video_type'] == 'stream':
            stream_info = {
                'name': video['name'],
                'video_id': video['video_id'],
                'thumbnail_url': video['thumbnail_url'],
                'duration': 0,
                'payload': video['payload']
            }
            curator_link = CuratorLink.objects.get_video_link(video['url'], stream_info)
            new_playlist = curator_link.create_new_playlist(channel)
        else:
            try:
                curator_link = CuratorLink.objects.get_video_link(video['url'])
            except (ValueError, LookupError) as e:
                logger.warn('Error add_video %s, skipping', video['url'])
                logger.exception(e)
                continue    # skip this video
            new_playlist = curator_link.create_new_playlist(channel, name=video['name'], detail=video.get('payload', None))

    if new_playlist is not None:
        new_playlist.pin()

    return render_json_response({'success': True})


@csrf_exempt
@atomic
def add_kodhit(request):
    """
        To make link as dailymotion but use kodhit url as an id
    """
    data = json.loads(request.body)
    links = data['links']
    channel_id = int(data['channel'])
    channel = CuratorChannel.objects.get(id=channel_id)
    all_links = []
    playlists = CuratorPlaylist.objects.filter(channel=channel)
    for playlist in playlists:
        if playlist.link is not None:
            all_links.append(playlist.link)
    for l in links:
        clink = CuratorLink.objects.filter(url=l['url']).first()
        if not clink:
            try:
                clink = CuratorLink.objects.get_video_link(l['video_id'])
            except Exception as e:
                logger.error(traceback.format_exc())
        if not clink:
            continue
        create = clink not in all_links
        dailymotion_id = CuratorLink.objects.get_video_id_from_url(l['video_id'])
        if clink.url == l['url'] and clink.video_id == dailymotion_id:
            pass
        else:
            clink.url = l['url']
            clink.video_id = dailymotion_id
            clink.save()
        if create:
            clink.create_new_playlist(channel, name=l['name'])
    return render_json_response({'success': True})


@csrf_exempt
def add_outstanding(request):
    links = request.POST.getlist("link", [])
    link_count = len(links)
    autoFlag = request.POST["autoPlayListFlag"]
    channelId = request.POST["channel"]
    channel = CuratorChannel.objects.get(id=channelId)

    new_playlist = None
    for link in links:
        data = json.loads(link)
        curator_link = CuratorLink.objects.get_video_link('http://www.youtube.com/watch?v=' + data['videoId'])
        new_playlist = curator_link.create_new_playlist(channel)

    if new_playlist is not None:
        new_playlist.pin()

    return render_to_response("addplaylist.html", {'channel': channelId, 'playlist': new_playlist.name,
                                                   'channel_name': channel.name, 'link_count': link_count})


@csrf_exempt
def tags_query(request):
    word = request.GET.get('word', '')
    source = request.GET.get('source', 'penta')

    if word == '':
        curatorTags = CuratorTag.objects.filter(show_in_listpage=True).order_by("show_in_listpage_index")
        if source == 'mobile':
            curatorTags = curatorTags.exclude(id__in=[120, 126, 142])
        else:
            curatorTags = curatorTags.exclude(id=304)
    else:
        curatorTags = CuratorTag.objects.filter(name__contains=word)[:50]

    tags = [{'id': curatorTag.id, 'name': curatorTag.name, 'name_en': curatorTag.name_en} for curatorTag in curatorTags]
    return render_json_response(tags)


@csrf_exempt
def tags_add(request):
    word = request.GET.get('word', '')
    if word == '':
        return render_json_response({'success': False, 'error': 'tag name can\'t be empty.'})
    else:
        curatorTags = CuratorTag.objects.filter(name=word)
        if len(curatorTags) == 0:
            curatorTag = CuratorTag()
            curatorTag.name = word
            curatorTag.save()
            return render_json_response({'success': True, "id": curatorTag.id, "name": curatorTag.name})
        else:
            curatorTag = curatorTags[0]
            return render_json_response({'success': True, 'error': 'tag name has already existed.', 'id': curatorTag.id,
                                         "name": curatorTag.name})


class QuerySetChain(object):
    """
    Chains multiple subquerysets (possibly of different models) and behaves as
    one queryset.  Supports minimal methods needed for use with
    django.core.paginator.
    """

    def __init__(self, *subquerysets):
        self.querysets = subquerysets

    def count(self):
        """
        Performs a .count() for all subquerysets and returns the number of
        records as an integer.
        """
        return sum(qs.count() for qs in self.querysets)

    def _clone(self):
        "Returns a clone of this queryset chain"
        return self.__class__(*self.querysets)

    def _all(self):
        "Iterates records in all subquerysets"
        return chain(*self.querysets)

    def __getitem__(self, ndx):
        """
        Retrieves an item or slice from the chained set of results from all
        subquery sets.
        """
        if type(ndx) is slice:
            return list(islice(self._all(), ndx.start, ndx.stop, ndx.step or 1))
        else:
            return islice(self._all(), ndx, ndx + 1).next()


class SearchList(APIView):
    authentication_classes = []
    permission_classes = []
    """
    /apis/search/ for PentaSearch in PentaRemote
     - it display SoopVideo, PentaChannel, then youtube video
    """
    def paginate_result(self, keyword, offset=0, pageToken=None, perPage=20):
        # search for PentaChannel, and youtube
        if offset <= 0:
            pageN = 1
        else:
            pageN = (offset / perPage) + 1

        soopvideos = SoopVideo.objects.with_keyword(keyword)
        channels = CuratorChannel.objects.with_keyword(keyword)
        youtube_result = my_youtube.search(keyword, pageToken=pageToken)

        channel_found = channels.count()
        soobvideos_found = soopvideos.count()
        total_count = channel_found + soobvideos_found + youtube_result['count']

        quries = QuerySetChain(channels, soopvideos)
        p = Paginator(quries, perPage)
        if (pageN <= p.num_pages):
            pageX = p.page(pageN)
            listPageX = list(pageX)
        else:
            listPageX = []

        if len(listPageX) < perPage:
            listPageX += youtube_result['results']

        # page links
        prev = None
        next = None
        if offset - perPage >= 0:
            prev = {'keyword': keyword.encode('utf8'),
                    'offset': offset - perPage}
        if offset + perPage < total_count:
            next = {'keyword': keyword.encode('utf8'),
                    'offset': offset + perPage}
        if offset + perPage >= channel_found + soobvideos_found:
            # paginate on youtube result
            if prev and youtube_result['prevPageToken']:
                prev['pageToken'] = youtube_result['prevPageToken']
            if youtube_result['nextPageToken']:
                next['pageToken'] = youtube_result['nextPageToken']
            else:
                next = None

        # union of result
        results = SearchResultSerializer(listPageX)
        return {
            'count': total_count,
            'results': results.data(),
            'next': next,
            'prev': prev,
        }

    def get(self, request, format=None):
        keyword = request.GET.get('keyword', '')
        try:
            offset = int(request.GET.get('offset', '0'))
        except ValueError:
            offset = 0
        pageToken = request.GET.get('pageToken', None)
        result = self.paginate_result(keyword, offset, pageToken)
        for k in ['next', 'prev']:
            if result[k]:
                result[k] = request.build_absolute_uri('?' + urllib.parse.urlencode(result[k]))
        return Response(result)


class YoutubePlaylist(APIView):
    authentication_classes = []
    permission_classes = []
    """Simulate youtube playlist as PentaChannel"""

    def get(self, request, playlist_id=None, format=None):
        playlist = my_youtube.get_playlist_info(playlist_id)
        if playlist:
            # add queue to playlist
            videos = list(my_youtube.videos_in_playlist(playlist_id))
            playlist['queue'] = list(map(youtube_video_to_queueitem, videos))
            if len(playlist['queue']) > 0:
                playlist['pin_queue_id'] = playlist['queue'][0]['queue_id']
            return Response(playlist)
        return Response(status=status.HTTP_404_NOT_FOUND)


# =========================== APIs v2 =========================== #

def remove_parameter(request_data, name):
    if hasattr(request_data, 'dicts'):
        for d in request_data.dicts:
            if name in d:
                d.pop(name)
                return
    else:
        for d in request_data:
            if name == d:
                request_data.pop(name)
                return


def remove_parameter_if_blank(request_data, name):
    if hasattr(request_data, 'dicts'):
        for d in request_data.dicts:
            if name in d:
                if not d[name]:
                    d.pop(name)
                    return
    else:
        for d in request_data:
            if name == d:
                if not request_data[d]:
                    request_data.pop(name)
                    return


class CustomAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


# ============ Tag ============ #

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_tag_highlight(request):

    source = request.GET.get('source', 'penta')
    tags = CuratorTag.objects.filter(show_in_listpage=True).order_by("show_in_listpage_index")

    if source == 'mobile':
        tags = tags.exclude(id__in=(120, 126, 142))
    else:
        tags = tags.exclude(id=304)

    serializer = CuratorTagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_tag_query(request):
    """
    GET  ->  /api/v2/tag/query/            = get all highlight tags
    GET  ->  /api/v2/tag/query/?q=<word>   = get all tags those contain <word>
    """
    word = request.GET.get('q', '')
    isAll = request.GET.get('mode')
    if not word:
        tags = CuratorTag.objects.filter(show_in_listpage=True).order_by("show_in_listpage_index")
        if request.user.is_anonymous() or not request.user.is_staff:
            tags = tags.exclude(id__in=[settings.TAG_LIVE_CHANNEL_ID])
        if not isAll:
            tags = tags.exclude(id__in=[settings.TAG_POPULAR_ID, settings.TAG_NEW_CHANNEL_ID])
    else:
        tags = CuratorTag.objects.filter(name__contains=word)[:50]

    serializer = CuratorTagSerializer(tags, many=True)
    return Response(serializer.data)


class APIv2TagManagerView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # check permission
        if request.user.is_anonymous() or not request.user.email in SUPER_ADMIN_LIST:
            raise PermissionDenied
        tag_id = request.GET.get('tag_id', None)
        if tag_id:
            channels = []
            if int(tag_id) == -1:
                channels_no_tag = CuratorChannel.objects.filter(tags=None, is_create_from_auto=False, isPrivate=False, user_save=False, user_share=False)
                for c in channels_no_tag:
                    channels.append({'id': c.id, 'name': c.name, 'can_show': False })
            else:
                channels_by_tag = CuratorChannel.objects.filter(tags__id=int(tag_id), isPrivate=False, user_save=False).order_by('name')
                for c in channels_by_tag:
                    channels.append({'id': c.id, 'tid': int(tag_id), 'name': c.name, 'can_show': True, 'show': c.channel_show.filter(id=int(tag_id)).count() > 0})
            return Response(channels)
        else:
            # add show item first
            tags = []
            show_tags = CuratorTag.objects.filter(show_in_listpage=True).order_by("show_in_listpage_index")
            for t in show_tags:
                tags.append({'id': t.id, 'name': t.name, 'show': True, 'show_index': t.show_in_listpage_index})
            no_show_tags = CuratorTag.objects.filter(show_in_listpage=False).order_by("name")
            for t in no_show_tags:
                tags.append({'id': t.id, 'name': t.name, 'show': False, 'show_index': t.show_in_listpage_index})
            return Response(tags)

    def post(self, request):
        # check permission
        if request.user.is_anonymous() or not request.user.email in SUPER_ADMIN_LIST:
            raise PermissionDenied
        tags = request.data.get('tags', None)
        if tags:
            tags_info = {}
            idx = 1
            for t in tags:
                tid = t['id']
                if t['show']:
                    tags_info[tid] = { 'show': True, 'idx': idx }
                    idx += 1
                else:
                    tags_info[tid] = { 'show': False, 'idx': 0 }
            with transaction.atomic():
                all_tags = CuratorTag.objects.all().only('id')
                for t in all_tags:
                    if t.id in tags_info:
                        t.show_in_listpage = tags_info[t.id]['show']
                        t.show_in_listpage_index = tags_info[t.id]['idx']
                        t.save()
                # transaction.commit()
            return Response(True)
        channel_show = request.data.get('channel_show', None)
        if channel_show:
            group_by_tag = {}
            channel_id = []
            channel_id_show = {}
            for c in channel_show:
                tid = c['tid']
                if not tid in group_by_tag:
                    group_by_tag[tid] = []
                cid = c['id']
                group_by_tag[tid].append(cid)
                channel_id.append(cid)
                channel_id_show[cid] = c['show']
            with transaction.atomic():
                target_channel = CuratorChannel.objects.in_bulk(channel_id)
                for tid in group_by_tag:
                    tag = CuratorTag.objects.get(id=tid)
                    for cid in group_by_tag[tid]:
                        if channel_id_show[cid]:
                            tag.channel_show.add(target_channel[cid])
                        else:
                            tag.channel_show.remove(target_channel[cid])
                # transaction.commit()
            return Response(True)
        return Response(False)


@api_view(['POST'])
def api_v2_tag_add(request):
    """
    POST  ->  /api/v2/tag/add/      = create new tag

    Post parameter
      'word'  STRING   new tag's name
    """
    word = request.data.get('word', '')
    if word == '':
        raise CustomAPIException('tag name can\'t be empty.')

    try:
        tag, is_new = CuratorTag.objects.get_or_create(name=word)
    except CuratorTag.MultipleObjectsReturned:
        # fix duplicated tags
        tags = CuratorTag.objects.filter(name=word)
        for tag in tags[1:]:
            tag.delete()
        tag = tags[0]

    serializer = CuratorTagSerializer(tag)
    return Response(serializer.data)


# ============ Channel ============= #

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def api_v2_add_pin_queue(request):


    user = request.user
    if user.is_anonymous():
        raise PermissionDenied
    playlist_id = request.data.get('playlist_id', '')

    try:
        if playlist_id:
            P = CuratorPlaylist.objects.get(id = int(playlist_id))
            UserHaveChannel.objects.filter(user = user , curatorChannel = P.channel).update(pin_queue = int(playlist_id))
            CuratorChannel.objects.filter(user = user , id = P.channel.id).update(pin_queue = int(playlist_id))
        return Response(json.dumps({"log":"success"}))
    except:
        log = traceback.format_exc()
        return Response(status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_latest_channels(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    channels = CuratorChannel.objects.filter(access_level=AccessLevel.ANY, user_save=False, isPrivate=False, is_create_from_auto=False).exclude(curatorplaylist=None).order_by('-create_at')
    paginator = Paginator(channels, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)
    serializer = CuratorChannelSummarySerializer(page_contents, many=True)
    return Response({'channels': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


def hour4earlier():
    return timezone.now()-timedelta(hours=4)


def day1earlier():
    return timezone.now()-timedelta(days=1)


def day3earlier():
    return timezone.now()-timedelta(days=3)


def day7earlier():
    return timezone.now()-timedelta(days=7)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_latest_channels_by_user(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    user = request.user
    if user.is_anonymous():
        return Response({})
    channel_items = CuratorUserWatched.objects.filter(user=user, curatorPlaylist__channel__user_save=False).values_list('curatorPlaylist__channel').annotate(m=Max('created')).order_by('-m')
    target_channel_ids = [f[0] for f in channel_items]
    channels_map = CuratorChannel.objects.in_bulk(target_channel_ids)
    channels = [channels_map[k] for k in target_channel_ids]
    paginator = Paginator(channels, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)

    serializer = CuratorChannelSummarySerializer(page_contents, many=True)

    return Response({'channels': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_highlight_channel(request):
    pass
    # page = request.GET.get('page', 1)
    # per_page = request.GET.get('per_page', 40)
    # channels = CuratorChannel.objects.filter(curatorviews__updated__gte=day3earlier()).exclude(user_save=True).order_by('-curatorviews__views')
    # paginator = Paginator(channels, per_page)
    # try:
    #     page_contents = paginator.page(page)
    # except PageNotAnInteger:
    #     page_contents = paginator.page(1)
    # except EmptyPage:
    #     page_contents = paginator.page(paginator.num_pages)

    # serializer = CuratorChannelSummarySerializer(page_contents, many=True)

    # return Response({'channels': serializer.data,
    #                  'has_other_pages': page_contents.has_other_pages(),
    #                  'page': page_contents.number,
    #                  'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_random_channel(request):
    amount = int(request.GET.get('amount', 8))
    data = list(CuratorChannel.objects.filter(access_level=AccessLevel.ANY)
                .exclude(Q(user_save=True) | Q(name='') |
                         Q(user_share=True) | Q(curatorplaylist=None) |
                         Q(is_create_from_auto=True)))
    channels = random.sample(data, min(amount, len(data)))
    serializer = CuratorChannelSummarySerializer(channels, many=True)
    return Response({'channels': serializer.data,})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_get_channel_from_tag(request, tag_id):
    source = request.GET.get('source', 'penta')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)

    tag = get_object_or_404(CuratorTag, id=tag_id)
    tag_name = tag.name

    if tag_id == str(settings.TAG_POPULAR_ID):
        channels = (CuratorChannel.objects
                    .filter(isPrivate=False, user_save=False, access_level=AccessLevel.ANY)
                    .exclude(curatorplaylist=None).order_by('-rank_score', 'id'))
    elif tag_id == str(settings.TAG_NEW_CHANNEL_ID):
        channels = (CuratorChannel.objects.filter(isPrivate=False, user_save=False)
                    .exclude(Q(tags=None) | Q(curatorplaylist=None)).order_by('-create_at'))
    else:
        channels = (CuratorChannel.objects.filter(access_level=AccessLevel.ANY, tags=tag_id)
                    .exclude(curatorplaylist=None).order_by('-rank_score', 'id'))

    if source == 'mobile':
        channels = channels.exclude(tags__in=[120, 126, 142])  # sensitive cases
    # else:
    #     channels = channels.exclude(tags=304)  # Composite channel not display on boxes

    paginator = Paginator(channels, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)
    serializer = CuratorChannelSummarySerializer(page_contents, many=True)
    return Response({'tag': tag_name,
                     'channels': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


def get_unwatch_count(channel, pin_queue=None):
    if pin_queue is None:
        pin_queue = channel.pin_queue
    playlist_index = list(channel.playlists().values_list('id', flat=True))
    if not pin_queue:
        unwatch_count = len(playlist_index)
    else:
        try:
            unwatch_count = len(playlist_index) - playlist_index.index(pin_queue) - 1
        except ValueError:
            unwatch_count = len(playlist_index)
    if unwatch_count < 0:
        return 0
    return unwatch_count


def updateMirror(channel_id, enable, y_user_id=None, y_channel_id=None,
                 y_playlist_id=None, include=None, exclude=None,
                 instant_add=True, latest_first=True,
                 publish_before=None, publish_after=None):
    # Currently channel can have only one mirror
    logger.debug('updateMirror')
    try:
        mirror, created = CuratorMirror.objects.get_or_create(channel_id=channel_id)
        mirror.active = bool(enable)
        mirror.youtube_user_id = y_user_id
        mirror.youtube_channel_id = y_channel_id
        mirror.youtube_playlist_id = y_playlist_id
        mirror.instant_add = bool(instant_add)
        mirror.latest_first = bool(latest_first)
        mirror.must_publish_after = publish_after
        mirror.must_publish_before = publish_before
        mirror.latest_sync = timezone.now()
        mirror.curatormirrorrule_set.all().delete()
        if enable:
            if not y_user_id or y_user_id.strip() == '':
                if not y_channel_id or y_channel_id.strip() == '':
                    if not y_playlist_id or y_playlist_id.strip() == '':
                        if not include or include.strip() == '':
                            if not exclude or exclude.strip() == '':
                                mirror.active = False
        mirror.save()
        if include:
            words = include.split(',')
            for w in set(words):
                CuratorMirrorRule.objects.create(mirror=mirror, keyword=w.strip(), rule=CuratorMirrorRule.INCLUDE_RULE)
        if exclude:
            words = exclude.split(',')
            for w in set(words):
                CuratorMirrorRule.objects.create(mirror=mirror, keyword=w.strip(), rule=CuratorMirrorRule.EXCLUDE_RULE)
        if enable:
            get_new_video_from_auto(channel_id, logger=logger)
    except Exception as e:
        logger.exception('updateMirror ERROR!')


class APIv2ChannelView(APIView):
    """
    get, create, edit, delete a channel

    GET    -> /api/v2/channel/              = get all user's channels and user's following channels
    GET    -> /api/v2/channel/<channel_id>/ = get
    POST   -> /api/v2/channel/              = create
    POST   -> /api/v2/channel/<channel_id>/ = update
    DELETE -> /api/v2/channel/<channel_id>/ = delete

    Post parameters
      'name'            STRING      channel name
      'icon'            IMAGE       icon of channel
      'icon_url'        URL         optional url of icon of channel
      'detail'          STRING      detail of channel
      'url_name'        STRING      look at /<user id>/channel/create/ and open advance for more detail
      'enable_auto'     BOOLEAN     to indicate that auto system should fetch video from rules
      'rule_include'    STRING      rule for auto system to include these keyword in result
      'rule_exclude'    STRING      rule for auto system to exclude these keyword in result
      'youtube_user_id_auto'  STRING  auto system search videos in this youtube channel id
      'youtube_channel_id_auto'  STRING  auto system search videos in this youtube channel id
      'youtube_playlist_id_auto'  STRING  auto system search videos in this youtube playlist id
      'instant_add'     BOOLEAN     instant video to channel instead of suggest system
      'latest_first'    BOOLEAN     to tell auto system to get new video first
      'publish_after'   datetime    only video publish after this specific time
      'publish_before'  datetime    only video publish before this specific time
      'tags'     [INT, ...] list of id of tags (room id)
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsChannelOwnerOrReadOnly)

    def get(self, request, channel_id=None):
        # self.check_permissions(request)
        if channel_id:
            channel = get_object_or_404(CuratorChannel, id=channel_id)
            if channel.user_save and (request.user.is_anonymous() or (channel.user != request.user) or (not request.user.email.lower() in SUPER_ADMIN_LIST)):
                raise PermissionDenied
            ret = CuratorChannelFullTagSerializerWithTag(channel , context={'request': request}).data
            ret['follow'] = False
            ret['subscribed'] = False
            ret['access_level_choices'] = dict(ACCESS_LEVEL_CHOICES)
            if not request.user.is_anonymous():
                try:
                    uhc = channel.followers.get(user=request.user)
                    ret['follow'] = True
                    ret['subscribed'] = uhc.subscribed
                except UserHaveChannel.DoesNotExist:
                    pass
                try:
                    mirror = channel.curatormirror_set.first()
                    if mirror:
                        ret['enable_auto'] = mirror.active
                        ret['instant_add'] = mirror.instant_add
                        ret['latest_first'] = mirror.latest_first
                        if mirror.youtube_playlist_id:
                            ret['youtube_playlist_id_auto'] = mirror.youtube_playlist_id
                        elif mirror.youtube_channel_id:
                            ret['youtube_channel_id_auto'] = mirror.youtube_channel_id
                        elif mirror.youtube_user_id:
                            ret['youtube_user_id_auto'] = mirror.youtube_user_id
                        include_rule = []
                        exclude_rule = []
                        for r in mirror.curatormirrorrule_set.all():
                            if r.rule == CuratorMirrorRule.INCLUDE_RULE:
                                include_rule.append(r.keyword)
                            else:
                                exclude_rule.append(r.keyword)
                        ret['rule_include'] = ','.join(include_rule)
                        ret['rule_exclude'] = ','.join(exclude_rule)
                        if mirror.must_publish_after:
                            ret['publish_after'] = mirror.must_publish_after.strftime("%d/%m/%Y %H:%M:%S")
                        if mirror.must_publish_before:
                            ret['publish_before'] = mirror.must_publish_before.strftime("%d/%m/%Y %H:%M:%S")
                    else:
                        ret['enable_auto'] = False
                        ret['instant_add'] = True
                        ret['latest_first'] = True
                except Exception as e:
                    pass
                ret['enable_sort_pattern'] = channel.enable_sort_pattern
                ret['episode_pattern'] = channel.episode_pattern
                ret['video_part_pattern'] = channel.video_part_pattern
                ret['auto_sort'] = channel.auto_sort
                ret['desc_sort'] = channel.desc_sort
            return Response(ret)
        else:
            if request.user.is_anonymous():
                raise PermissionDenied
            own_channels = CuratorChannel.objects.exclude(is_sqool=True).filter(user=request.user, user_share=False, user_save=False) \
                .order_by('name')
            own_channels_dict = []
            # modify to show unread_count > 0 first
            own_channels_dict_read = []
            for channel in own_channels:
                data = CuratorChannelSummarySerializer(channel , context={'request': request}).data
                data['unread_count'] = channel.suggested_links.filter(is_read=False).count()

                """
                try: #already add in serializer
                    data['latest_playlist'] = channel.curatorplaylist_set.latest("id").name
                except CuratorPlaylist.DoesNotExist:
                    data['latest_playlist'] = ''
                """

                if data['unread_count'] > 0:
                    own_channels_dict.append(data)
                else:
                    own_channels_dict_read.append(data)
            own_channels_dict.extend(own_channels_dict_read)

            saved_channel = request.user.userdetail.get_saved_channel()
            saved_channel_dict = CuratorChannelSummarySerializer(saved_channel , context={'request': request}).data
            saved_channel_dict['unwatch_count'] = get_unwatch_count(saved_channel)

            user_have_channels = UserHaveChannel.objects.filter(user=request.user)\
                .select_related('curatorChannel').order_by('-curatorChannel__update_at')
            following_channel_dict = []
            for uhc in user_have_channels:
                if uhc.curatorChannel is None:
                    uhc.delete()
                    continue
                channel = uhc.curatorChannel
                data = CuratorChannelSummarySerializer(channel, context={'request': request}).data
                #PENG ADD FOR PROVIDE PENTACENTER APP
                #data['latest_playlist'] = ''
                #if channel.curatorplaylist_set.all().first(): data['latest_playlist'] = channel.curatorplaylist_set.all().order_by("-id")[0].name
                """
                try: #already add in serializer
                    data['latest_playlist'] = channel.curatorplaylist_set.latest("id").name
                except CuratorPlaylist.DoesNotExist:
                    data['latest_playlist'] = ''
                """

                ###
                data['unwatch_count'] = get_unwatch_count(channel, uhc.pin_queue)
                following_channel_dict.append(data)

            ret = {
                'share': CuratorChannelSummarySerializer(request.user.userdetail.get_share_channel(), context={'request': request}).data,
                'saved': saved_channel_dict,
                'own': own_channels_dict,
                'follow': following_channel_dict,
                'access_level_choices': dict(ACCESS_LEVEL_CHOICES),
            }
            if request.user.email in SUPER_ADMIN_LIST:
                ret['admin'] = request.user.id
            return Response(ret)

    def post(self, request, channel_id=None):
        auto_enable = request.data.get('enable_auto', False)
        youtube_user_id_auto = request.data.get('youtube_user_id_auto', None)
        youtube_channel_id_auto = request.data.get('youtube_channel_id_auto', None)
        youtube_playlist_id_auto = request.data.get('youtube_playlist_id_auto', None)
        instant_add = request.data.get('instant_add', True)
        latest_first = request.data.get('latest_first', True)
        rule_include = request.data.get('rule_include', None)
        rule_exclude = request.data.get('rule_exclude', None)
        publish_before = request.data.get('publish_before', None)
        publish_after = request.data.get('publish_after', None)

        enable_sort_pattern = request.data.get('enable_sort_pattern ', False)
        episode_pattern = request.data.get('episode_pattern ', '')
        video_part_pattern = request.data.get('video_part_pattern ', '')
        auto_sort = request.data.get('auto_sort ', False)
        desc_sort = request.data.get('desc_sort ', False)
        if publish_before:
            try:
                publish_before = timezone.make_aware(datetime.strptime(publish_before, '%d/%m/%Y %H:%M:%S'), timezone.utc)
            except:
                publish_before = None
        if publish_after:
            try:
                publish_after = timezone.make_aware(datetime.strptime(publish_after, '%d/%m/%Y %H:%M:%S'), timezone.utc)
            except:
                publish_after = None

        if channel_id:
            channel = get_object_or_404(CuratorChannel, id=channel_id)

            tags = []
            if 'tags[0]' in request.data:
                i = 0
                while 'tags[%d]' % i in request.data:
                    tags.append(request.data['tags[%d]' % i])
                    i += 1
            else:
                tags = request.data.get('tags', [])

            # print request.data

            self.check_object_permissions(request, channel)
            serializer = CuratorChannelSerializerWithTag(instance=channel, data=request.data, partial=True,
                                                         context={'request': request})
            serializer.tags = tags
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # remove channel show that not contain in channel's tags
            dangling_tag = channel.channel_show.exclude(id__in=channel.tags.values_list('id', flat=True))
            for t in dangling_tag:
                channel.channel_show.remove(t)

            updateMirror(channel_id, auto_enable, y_user_id=youtube_user_id_auto, y_channel_id=youtube_channel_id_auto,
                         y_playlist_id=youtube_playlist_id_auto, include=rule_include, exclude=rule_exclude,
                         instant_add=instant_add, latest_first=latest_first, publish_before=publish_before,
                         publish_after=publish_after)

            return Response(serializer.data)
        else:
            self.check_permissions(request)

            tags = []
            if 'tags[0]' in request.data:
                i = 0
                while 'tags[%d]' % i in request.data:
                    tags.append(request.data['tags[%d]' % i])
                    i += 1
            else:
                tags = request.data.get('tags', [])

            remove_parameter_if_blank(request.data, 'icon')
            remove_parameter(request.data, 'tags')

            # print request.data, type(request.data)
            # print tags, type(tags)

            serializer = CuratorChannelSerializerWithTag(instance=CuratorChannel(user=request.user),
                                                         data=request.data, partial=True,
                                                         context={'request': request})
            serializer.is_valid(raise_exception=True)
            channel = serializer.save()
            if tags:
                serializer = CuratorChannelSerializerWithTag(instance=channel, data={"tags": tags},
                                                             partial=True, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save()

            updateMirror(channel.id, auto_enable, y_user_id=youtube_user_id_auto,
                         y_channel_id=youtube_channel_id_auto, y_playlist_id=youtube_playlist_id_auto,
                         include=rule_include, exclude=rule_exclude, instant_add=instant_add,
                         latest_first=latest_first, publish_before=publish_before, publish_after=publish_after)

            # add first video for channel
            first_video = request.data.get('first_video', None)
            if first_video:
                try:
                    link = CuratorLink.objects.get_video_link(first_video)
                    if link:
                        link.create_new_playlist(channel)
                except Exception as e:
                    logger.exception(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, channel_id=None):
        channel = get_object_or_404(CuratorChannel, id=channel_id)
        self.check_object_permissions(request, channel)
        channel.delete()
        return Response(True)


class APIv2ChannelPlaylistView(APIView):
    """
    get playlist in channel
    GET  -> /api/v2/channel/<channel_id>/playlist/?page=<n>&per_page=<m>  = get playlist from channel
    POST -> /api/v2/channel/<channel_id>/playlist/                        = add existing playlist to channel

    Post parameters
    link      INT     id of the link (optional)
    playlist  INT     id of the playlist (optional)
    detail    STRING  detail for new playlist
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @cache_response_anonymous_only(timeout=60, key_func=calculate_key_for_cache) # 1 min
    def get(self, request, channel_id):
        user = request.user
        channel = get_object_or_404(CuratorChannel, id=channel_id)
        if channel.access_level > AccessLevel.ANY and (user.is_anonymous() or (channel.user != user and user.email not in SUPER_ADMIN_LIST)):
            raise PermissionDenied
        if request.user.is_authenticated():
            # Clear unwatch count
            UserHaveChannel.objects.filter(curatorChannel=channel , user=user).update(unwatch_count=0)
        access_level = AccessLevel.ANY
        if not user.is_anonymous() and (channel.user == user or user.email in SUPER_ADMIN_LIST):
            access_level = AccessLevel.PENTA
        ret = CuratorChannelSummarySerializer(channel).data
        reverse = request.GET.get('reverse', False)
        order = 'playlist_index' if reverse else '-playlist_index'
        playlists = channel.playlists().filter(sub_access_level__lte=access_level).select_related('link')\
            .prefetch_related('tags', 'curatorviews_set', 'user_like')\
            .annotate(Count('user_like')).order_by(order)  # override default order from playlists()
        page = request.GET.get('page')
        per_page = request.GET.get('per_page', 40)
        paginator = Paginator(playlists, per_page)
        try:
            page_contents = paginator.page(page)
        except PageNotAnInteger:
            page_contents = paginator.page(1)
        except EmptyPage:
            page_contents = paginator.page(paginator.num_pages)
        ret['playlists'] = CuratorPlaylistLinkSerializer(page_contents.object_list, many=True,
                                                         context={'request': request}).data
        ret['has_other_pages'] = page_contents.has_other_pages()
        ret['page'] = page_contents.number
        ret['num_page'] = paginator.num_pages
        return Response(ret)

    def post(self, request, channel_id):
        channel = get_object_or_404(CuratorChannel, id=channel_id)
        if channel.user != request.user and request.user.email not in SUPER_ADMIN_LIST:
            raise PermissionDenied
        link_id = request.data.get('link')
        playlist_id = request.data.get('playlist')
        detail = request.data.get('detail', "")

        if link_id:
            link = get_object_or_404(CuratorLink, pk=link_id)
            new_playlist = link.create_new_playlist(channel, detail=detail)
        elif playlist_id:
            playlist = get_object_or_404(CuratorPlaylist, pk=playlist_id)
            new_playlist = playlist.link.create_new_playlist(channel, detail=detail)
        else:
            raise CustomAPIException("need parameter 'link' or 'playlist'")

        if new_playlist:
            serializer = CuratorPlaylistLinkSerializer(new_playlist)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise APIException("Something went wrong!")


@api_view(['POST'])
def api_v2_follow_channel(request, channel_id):
    """Follow user to channel"""
    if request.user.is_anonymous():
        raise PermissionDenied
    channel = get_object_or_404(CuratorChannel, id=channel_id)
    UserHaveChannel.objects.get_or_create(user=request.user, curatorChannel=channel)
    return Response({'detail': 'success',
                     'channel': CuratorChannelSummarySerializer(channel).data
                     })


@api_view(['POST'])
def api_v2_unfollow_channel(request, channel_id):
    """Unfollow user from channel"""
    if request.user.is_anonymous():
        raise PermissionDenied
    channel = get_object_or_404(CuratorChannel, id=channel_id)
    try:
        uhc = UserHaveChannel.objects.get(user=request.user, curatorChannel=channel)
        uhc.delete()
        return Response({'detail': 'success',
                         'channel': CuratorChannelSummarySerializer(channel).data
                         })
    except UserHaveChannel.DoesNotExist:
        return Response({'detail': 'not followed yet'})


@api_view(['POST'])
def api_v2_subscribe_channel(request, channel_id):
    """Subscribe user to channel"""
    if request.user.is_anonymous():
        raise PermissionDenied
    channel = get_object_or_404(CuratorChannel, id=channel_id)
    user_have_channel = get_object_or_404(UserHaveChannel, user=request.user, curatorChannel=channel)
    user_have_channel.subscribed = True
    user_have_channel.save()
    return Response({'detail': 'success',
                     'channel': CuratorChannelSummarySerializer(channel).data
                     })


@api_view(['POST'])
def api_v2_unsubscribe_channel(request, channel_id):
    """Unsubscribe user to channel"""
    if request.user.is_anonymous():
        raise PermissionDenied
    channel = get_object_or_404(CuratorChannel, id=channel_id)
    user_have_channel = get_object_or_404(UserHaveChannel, user=request.user, curatorChannel=channel)
    user_have_channel.subscribed = False
    user_have_channel.save()
    return Response({'detail': 'success',
                     'channel': CuratorChannelSummarySerializer(channel).data
                     })


@api_view(['POST'])
def api_v2_remove_playlist_channel(request, channel_id):
    is_all = request.data.get('all', False)
    if request.user.is_anonymous():
        raise PermissionDenied
    target_channel = CuratorChannel.objects.filter(id=channel_id).first()
    if target_channel:
        if (request.user.email not in SUPER_ADMIN_LIST) and target_channel.user != request.user:
            raise PermissionDenied
        plq = target_channel.playlists()
        if not is_all:
            ids = request.data.get('id', '').split(',')
            playlist_ids = []
            for sid in ids:
                if not sid.isdigit():
                    raise CustomAPIException('empty or invalid id')
                playlist_ids.append(int(sid))
            plq = plq.filter(id__in=playlist_ids)
            # memorize which link user don't want in channel
            for p in plq:
                if p.from_rules_auto:
                    CuratorUserUnwantedLink.objects.get_or_create(channel=p.channel, link=p.link)
        plq.delete()
        return Response(True)
    else:
        raise CustomAPIException('invalid channel')


@api_view(['POST'])
def api_v2_reorder_playlist_channel(request, channel_id):
    ids = request.data.get('ordered_id', '').split(',')
    playlist_ids = []
    for sid in ids:
        if not sid.isdigit():
            raise CustomAPIException('empty or invalid id')
        playlist_ids.append(int(sid))
    if request.user.is_anonymous():
        raise PermissionDenied
    target_channel = CuratorChannel.objects.filter(id=channel_id).first()
    if target_channel and len(playlist_ids) > 0:
        if (not request.user.email in SUPER_ADMIN_LIST) and target_channel.user != request.user:
            raise PermissionDenied
        # remove invalid and duplicate playlist id
        final_playlist_ids = target_channel.playlists().filter(id__in=playlist_ids).values_list('id', flat=True)
        if len(final_playlist_ids) > 0:
            with transaction.atomic():
                final_playlist_ids = sorted(set(final_playlist_ids), key=lambda x: playlist_ids.index(x))
                min_playlist_index = (target_channel.playlists().filter(id__in=final_playlist_ids)
                                      .aggregate(min=Min('playlist_index'))['min'])
                index = 1
                # top group
                top_group = (target_channel.playlists().filter(playlist_index__lte=min_playlist_index)
                             .exclude(id__in=final_playlist_ids).order_by('playlist_index'))
                for pl in top_group:
                    pl.playlist_index = index
                    pl.save()
                    index += 1
                # middle group = order group
                middle_group = target_channel.playlists().filter(id__in=final_playlist_ids)
                for pl in middle_group:
                    pl.playlist_index = index + final_playlist_ids.index(pl.id)
                    pl.save()
                index += len(final_playlist_ids)
                # bottom group
                bottom_group = (target_channel.playlists().filter(playlist_index__gt=min_playlist_index)
                                .exclude(id__in=final_playlist_ids).order_by('playlist_index'))
                for pl in bottom_group:
                    pl.playlist_index = index
                    pl.save()
                    index += 1
                # transaction.commit()
            return Response(True)
    raise CustomAPIException('invalid channel')


@api_view(['POST'])
def api_v2_orderbyalphabet_playlist_channel(request, channel_id):
    if request.user.is_anonymous():
        raise PermissionDenied
    target_channel = CuratorChannel.objects.filter(id=channel_id).first()
    if target_channel:
        if request.user.email not in SUPER_ADMIN_LIST and target_channel.user != request.user:
            raise PermissionDenied
        if target_channel.playlists().exists():
            with transaction.atomic():
                i = 1
                for playlist in target_channel.playlists().only('id').order_by('-playlist_index'):
                    if playlist.playlist_index != i:
                        playlist.playlist_index = i
                        playlist.save()
                    i += 1
        return Response(True)
    raise CustomAPIException('invalid channel')


@api_view(['POST'])
def api_v2_orderby_pattern_playlist_channel(request, channel_id):
    if request.user.is_anonymous():
        raise PermissionDenied
    target_channel = CuratorChannel.objects.filter(id=channel_id).first()
    if target_channel:
        # print request.user.email
        if request.user.email not in SUPER_ADMIN_LIST and target_channel.user != request.user:
            raise PermissionDenied
        if target_channel.playlists().exists():
            try:
                target_channel.sort_videos_by_pattern()
            except Exception as e:
                logger.exception(e)
                raise CustomAPIException(e)
        return Response(True)
    raise CustomAPIException('invalid channel')


@api_view(['POST'])
def api_v2_channel_set_permission_for_all_playlists(request, channel_id):
    c = CuratorChannel.objects.filter(id=channel_id).first()
    if not c:
        raise CustomAPIException('invalid channel')
    if not has_edit_channel_permission(request.user, c):
        raise PermissionDenied
    level = request.data.get('level', None)
    # check specific level
    if level is None:
        raise CustomAPIException("No level specific")
    # check valid level
    if level not in dict(ACCESS_LEVEL_CHOICES):
        raise CustomAPIException("Target level not exists")
    c.curatorplaylist_set.update(sub_access_level=level)
    return Response(True)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_channel_create_init_data(request):
    ret = {}
    ret['access_level_choices'] = dict(ACCESS_LEVEL_CHOICES)
    return Response(ret)


# ============ Playlist ============= #

class APIv2PlaylistLatestVideo(APIView):
    authentication_classes = []
    permission_classes = []

    @cache_response(15*60)  # 15 minutes
    def get(self, request):
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 40)
        channel_ids = (CuratorPlaylist.objects.filter(channel__access_level=AccessLevel.ANY,
                                                      sub_access_level=AccessLevel.ANY,
                                                      channel__user_save=False,
                                                      channel__isPrivate=False)
                       .values_list('channel_id').annotate(m=Max('create_at')).order_by('-m'))
        paginator = Paginator(channel_ids, per_page)
        try:
            page_contents = paginator.page(page)
        except PageNotAnInteger:
            page_contents = paginator.page(1)
        except EmptyPage:
            page_contents = paginator.page(paginator.num_pages)
        playlists = []
        for (channel_id, create_at) in page_contents.object_list:
            result = CuratorPlaylist.objects.filter(channel_id=channel_id, create_at=create_at).first()
            if result:
                playlists.append(result)
        serializer = CuratorPlaylistLinkSerializer(playlists, many=True, context={'request': request})
        ret = {'playlists': serializer.data,
               'has_other_pages': page_contents.has_other_pages(),
               'page': page_contents.number,
               'num_page': paginator.num_pages}
        return Response(ret)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_playlist_latest_videos_by_user(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 8)
    total = int(page) * int(per_page)
    count = 0
    uniq_channel_playlists = []
    if not request.user.is_anonymous():
        exists = []
        playlists = (CuratorPlaylist.objects.filter(channel__followers__user=request.user)
                     .exclude(channel=settings.STAFF_PICK_CHANNEL).order_by('-create_at'))
        for item in playlists:
            if item.channel_id not in exists:
                exists.append(item.channel_id)
                uniq_channel_playlists.append(item)
                count += 1
            if count >= total:
                break
    paginator = Paginator(uniq_channel_playlists, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)

    serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})

    return Response({'playlists': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_highlight_playlist(request):
    base_key = "{0}?{1}".format(request.path, request.META['QUERY_STRING'])
    key = "hl_" + base_key
    key_time = "hlt_" + base_key
    ret = cache.get(key)
    last_sync = cache.get(key_time)
    renew = ret is None or last_sync is None or (last_sync + timedelta(minutes=10)) <= datetime.now()
    if renew:
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 40)
        playlists = (CuratorPlaylist.objects.filter(channel=settings.STAFF_PICK_CHANNEL)
                     .order_by('-playlist_index'))
        # Trending Channel 321
        paginator = Paginator(playlists, per_page)
        try:
            page_contents = paginator.page(page)
        except PageNotAnInteger:
            page_contents = paginator.page(1)
        except EmptyPage:
            page_contents = paginator.page(paginator.num_pages)
        serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})
        ret = {'playlists': serializer.data,
               'has_other_pages': page_contents.has_other_pages(),
               'page': page_contents.number,
               'num_page': paginator.num_pages}
        cache.set(key, ret)
        cache.set(key_time, datetime.now())
    return Response(ret)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_saved_unwatched(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    playlists = []
    if not request.user.is_anonymous():
        playlists = CuratorPlaylist.objects.filter(channel__user=request.user,
                                                   channel__user_save=True,
                                                   curatoruserwatched=None).order_by('-create_at')
    paginator = Paginator(playlists, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)

    serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})

    return Response({'playlists': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_playlist_followed(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    no_detail = request.GET.get('no_detail', False)
    new_only = request.GET.get('new_only', False)
    per_page = request.GET.get('per_page', 40)
    playlists = []
    count = 0
    if not request.user.is_anonymous():
        playlists = CuratorPlaylist.objects.filter(channel__followers__user=request.user).exclude(channel__user_save=True)
        last_visit_follow_page = request.user.userprofile.last_visit_follow_page
        if new_only and last_visit_follow_page:
            playlists = playlists.filter(create_at__gte=last_visit_follow_page)
        playlists = playlists.order_by('-create_at')
        count = playlists.count()
        if no_detail:
            playlists = []

    paginator = Paginator(playlists, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)

    serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})

    return Response({'playlists': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages,
                     'count': count})


@api_view(['POST'])
def api_v2_playlist_play_position(request, playlist_id):
    user = request.user
    if user.is_anonymous() or (user.email not in SUPER_ADMIN_LIST and
                               not CuratorPlaylist.objects.filter(id=playlist_id, channel__user=user).exists()):
        raise PermissionDenied

    pl = CuratorPlaylist.objects.filter(id=playlist_id).only('play_start_at', 'play_end_at').first()
    if pl:
        start_at = request.data.get('start', None)
        end_at = request.data.get('end', None)
        cancel = request.data.get('cancel', False)
        if cancel:
            pl.play_start_at = None
            pl.play_end_at = None
            pl.save()
            return Response(True)
        else:
            valid = False
            if start_at and start_at.isdigit() and int(start_at) >= 0:
                start = int(start_at) if int(start_at) > 0 else None
                pl.play_start_at = start
                valid = True
            if end_at and end_at.isdigit() and int(end_at) > 0:
                pl.play_end_at = int(end_at)
                valid = True
            if not valid:
                raise CustomAPIException("invalid, must specific at least start or end by value from 1")
            # start and end are set and case xor
            if (pl.play_start_at and pl.play_end_at and pl.play_start_at < pl.play_end_at) or \
            (pl.play_start_at == None and pl.play_end_at) or (pl.play_start_at and pl.play_end_at == None) or (pl.play_start_at == None and pl.play_end_at == None):
                pl.save()
                return Response(True)
            else:
                raise CustomAPIException("invalid start or end time")
    raise CustomAPIException("playlist not found")


@api_view(['POST'])
def api_v2_playlist_set_permission(request, playlist_id):
    user = request.user
    # check who can set permission
    if user.is_anonymous() or (user.email not in SUPER_ADMIN_LIST and
                               not CuratorPlaylist.objects.filter(id=playlist_id, channel__user=user).exists()):
        raise PermissionDenied
    pl = CuratorPlaylist.objects.filter(id=playlist_id).only('sub_access_level').first()
    if pl:
        level = request.data.get('level', None)
        # check specific level
        if level == None:
            raise CustomAPIException("No level specific");
        # check valid level
        if not level in dict(ACCESS_LEVEL_CHOICES):
            raise CustomAPIException("Target level not exists");
        pl.sub_access_level = level
        pl.save()
        return Response(True)
    raise CustomAPIException("playlist not found")


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_playlist_user_might_watch(request):
    """
    Not implemented
    """
    user = request.user
    ret = []
    if not user.is_anonymous():
        pass
    return Response([])


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_get_playlist_from_tag(request, tag_id):
    tag = get_object_or_404(CuratorTag, id=tag_id)
    tag_name = tag.name
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    playlists = (CuratorPlaylist.objects.filter(Q(channel__access_level=AccessLevel.ANY,
                                                  sub_access_level=AccessLevel.ANY) &
                                                (Q(channel__tags=tag_id) | Q(tags=tag_id)))
                 .order_by('-create_at').distinct())
    paginator = Paginator(playlists, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)
    serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})
    return Response({'tag': tag_name,
                     'playlists': serializer.data,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


WORKER_EXISTS = None


def is_worker_exists():
    global WORKER_EXISTS
    if WORKER_EXISTS is None:
        try:
            WORKER_EXISTS = True if celery.current_app.control.inspect().ping() else False
        except:
            WORKER_EXISTS = False
    return WORKER_EXISTS


# support only one tag_id
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_get_link_from_tag(request, tag_id):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    username = request.user.username if not request.user.is_anonymous() else None
    if is_worker_exists():
        key = 'get_link_tag_%s_%s_%s' % (tag_id, page, per_page)
        busy_key = '%s_busy' % key
        cached_result = cache.get(key)
        if cached_result is None:
            # print '[miss]', key
            cache.set(busy_key, False)
            final_result = update_get_link_from_tag(username, tag_id, page, per_page)
        else:
            # print '[hit]', key
            final_result, expiry = cached_result
            is_busy = cache.get(busy_key)
            # print '[status]', key, isBusy
            if not is_busy or expiry < datetime.now():
                cache.set(busy_key, True)
                update_get_link_from_tag.delay(username, tag_id, page, per_page)
    else:
        final_result = update_get_link_from_tag(username, tag_id, page, per_page, caching=False)
    # cache.set("xxx", finalResult, None)
    # check = cache.get("xxx")
    # print 'EQUAL', check == finalResult
    # print 'TOTAL', time.time()-start
    return Response(final_result)


class APIv2PlaylistView(APIView):
    """
    get, create, edit, delete a playlist

    GET    -> /api/v2/playlist/?channel=<id>,<id>,... = get all playlist in channels
    GET    -> /api/v2/playlist/<playlist_id>/ = get
    POST   -> /api/v2/playlist/               = create
    POST   -> /api/v2/playlist/<playlist_id>/ = update
    DELETE -> /api/v2/playlist/<playlist_id>/ = delete

    Post parameters
      'name'    STRING     playlist name
      'detail'  STRING     detail of playlist
      'channel' INT        channel id (for create)
      'tags'    [INT, ...] list of id of tags (room id)
      'url'     URL        url of video
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsPlaylistOwnerOrReadOnly)

    @cache_response_anonymous_only(timeout=60, key_func=calculate_key_for_cache) # 1 min
    def get(self, request, playlist_id=None):
        pin_queue = None
        access_level = AccessLevel.ANY
        if not request.user.is_anonymous() and request.user.email in SUPER_ADMIN_LIST:
            access_level = AccessLevel.PENTA

        if playlist_id is None:
            if 'channel' in request.GET:
                channel = request.GET['channel'].split(',')
                page = request.GET.get('page', 1)
                per_page = request.GET.get('per_page', 40)
                target_user = request.user
                if request.user.is_anonymous():
                    target_user = None
                if len(channel) > 1:
                    playlists = (CuratorPlaylist.objects.filter(Q(channel__in=channel) &
                                                                (Q(channel__user=target_user) |
                                                                 Q(channel__access_level__lte=access_level,
                                                                   sub_access_level__lte=access_level)))
                                 .order_by('-create_at'))
                elif len(channel) == 1:
                    playlists = (CuratorPlaylist.objects.filter(Q(channel=channel[0]) &
                                                                (Q(channel__user=target_user) |
                                                                 Q(channel__access_level__lte=access_level,
                                                                   sub_access_level__lte=access_level)))
                                 .order_by('-playlist_index'))
                    try:
                        pin_queue = UserHaveChannel.objects.get(user=request.user,
                                                                curatorChannel__id=int(channel[0])).pin_queue
                    except:
                        pin_queue = None
                else:
                    playlists = []

                paginator = Paginator(playlists, per_page)
                try:
                    page_contents = paginator.page(page)
                except PageNotAnInteger:
                    page_contents = paginator.page(1)
                except EmptyPage:
                    page_contents = paginator.page(paginator.num_pages)
                serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})
                return Response({'playlists': serializer.data,
                                 'has_other_pages': page_contents.has_other_pages(),
                                 'page': page_contents.number,
                                 'pin_queue': pin_queue,
                                 'num_page': paginator.num_pages})
            else:
                return Response({'detail': 'required parameter "channel"'}, status=status.HTTP_400_BAD_REQUEST)

        playlist = get_object_or_404(CuratorPlaylist, id=playlist_id)
        if request.user != playlist.channel.user and (playlist.sub_access_level > access_level or
                                                      playlist.channel.access_level > access_level):
            raise PermissionDenied
        return Response(CuratorPlaylistLinkSerializer(playlist, context={'request': request}).data)

    def post(self, request, playlist_id=None):
        if playlist_id is None:
            if not request.data.get('channel'):
                raise CustomAPIException('needs channel')
                # return Response({'detail': 'needs channel'}, status=status.HTTP_400_BAD_REQUEST)
            if not request.data.get('url'):
                raise CustomAPIException('needs url')
                # return Response({'detail': 'needs url'}, status=status.HTTP_400_BAD_REQUEST)
            name = request.data.get('name')
            detail = request.data.get('detail')
            channel = get_object_or_404(CuratorChannel, id=request.data.get('channel'))
            tags = request.data.get('tags', [])
            url = request.data.get('url')

            play_start_at = request.data.get('play_start_at')
            play_end_at = request.data.get('play_end_at')

            if channel.user != request.user and request.user.email not in SUPER_ADMIN_LIST:
                raise PermissionDenied
            try:
                link = CuratorLink.objects.get_video_link(url)
                if link.video_type == VideoType.STREAM_URL and not name:
                    name = channel.name
                playlist = link.create_new_playlist(channel, name=name, detail=detail, tags=tags,
                                                    play_start_at=play_start_at, play_end_at=play_end_at)
                serializer = CuratorPlaylistLinkSerializer(playlist, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except (LookupError, TypeError, ValueError) as e:
                return Response({'detail': e}, status=status.HTTP_400_BAD_REQUEST)
        playlist = get_object_or_404(CuratorPlaylist, id=playlist_id)
        remove_parameter_if_blank(request.data, 'tag')
        self.check_object_permissions(request, playlist)
        serializer = CuratorPlaylistSerializer(instance=playlist, data=request.data, partial=True,
                                               context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, playlist_id=None):
        playlist = get_object_or_404(CuratorPlaylist, id=playlist_id)
        self.check_object_permissions(request, playlist)
        if playlist.from_rules_auto:
            # memorize which link user don't want in channel before delete
            CuratorUserUnwantedLink.objects.get_or_create(channel=playlist.channel, link=playlist.link)
        # update playlist index
        CuratorPlaylist.objects.filter(channel=playlist.channel, playlist_index__gt=playlist.playlist_index).update(playlist_index=F('playlist_index')-1)
        playlist.delete()
        return Response(True)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_playlist_watched(request, playlist_id):
    # TODO log to database or file
    playlist = get_object_or_404(CuratorPlaylist, id=playlist_id)
    user = None
    if request.user.is_authenticated():
        user = request.user.username
    else:
        user = request.session.session_key
    return Response({
        'time': timezone.now(),
        'user': user,
        'playlist': playlist.name
    })


def api_v2_playlist_set_like(request, playlist, is_like):
    if request.user.is_anonymous():
        raise PermissionDenied
    user = request.user
    if is_like:
        if not User.objects.filter(id=user.id, curatorplaylist__id=playlist.id):
            playlist.user_like.add(user)
            return Response(True)
    else:
        if User.objects.filter(id=user.id, curatorplaylist__id=playlist.id):
            playlist.user_like.remove(user)
            return Response(True)


@api_view(['POST'])
def api_v2_playlist_like(request, playlist_id):
    """ User like this playlist """
    return api_v2_playlist_set_like(request, get_object_or_404(CuratorPlaylist, id=playlist_id), True)


@api_view(['POST'])
def api_v2_playlist_unlike(request, playlist_id):
    """ User unlike this playlist """
    return api_v2_playlist_set_like(request, get_object_or_404(CuratorPlaylist, id=playlist_id), False)


def api_v2_playlist_set_save(request, playlist, is_save):
    if request.user.is_anonymous():
        raise PermissionDenied
    saved_channel = request.user.userdetail.get_saved_channel()
    link = playlist.link
    saved_playlist = saved_channel.curatorplaylist_set.filter(link=link)

    if is_save:
        if not saved_playlist:
            saved_playlist = link.create_new_playlist(saved_channel)
        serializer = CuratorPlaylistLinkSerializer(saved_playlist, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        if saved_playlist:
            playlist = saved_playlist.first()
            serializer = CuratorPlaylistLinkSerializer(playlist, context={'request': request})
            data = serializer.data
            playlist.delete()
            return Response(data)
    return Response(False)


def api_v2_playlist_set_save_ex(request, src, src_id, is_save):
    if request.user.is_anonymous():
        raise PermissionDenied
    saved_channel = request.user.userdetail.get_saved_channel()
    if is_save:
        exists = saved_channel.playlists().filter(link__video_id=src_id, link__video_type=src).exists()
        if not exists:
            if src == VideoType.YOUTUBE:
                youtube_url = 'https://www.youtube.com/watch?v='
                link = CuratorLink.objects.get_video_link(youtube_url + src_id)
                link.create_new_playlist(saved_channel, name=link.name, detail=link.payload)
    else:
        saved_channel.playlists().filter(link__video_id=src_id, link__video_type=src).delete()
    return Response(False)


@api_view(['POST'])
def api_v2_playlist_save(request, playlist_id):
    """ User save this playlist """
    return api_v2_playlist_set_save(request, get_object_or_404(CuratorPlaylist, id=playlist_id), True)


@api_view(['POST'])
def api_v2_playlist_unsave(request, playlist_id):
    """ User unsave this playlist """
    return api_v2_playlist_set_save(request, get_object_or_404(CuratorPlaylist, id=playlist_id), False)


@api_view(['POST'])
def api_v2_playlist_save_ex(request, src, src_id):
    """ User save external src """
    return api_v2_playlist_set_save_ex(request, src, src_id, True)


@api_view(['POST'])
def api_v2_playlist_unsave_ex(request, src, src_id):
    """ User save external src """
    return api_v2_playlist_set_save_ex(request, src, src_id, False)


# ============ Link ============= #


# ============ Suggestion ============= #

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_user_suggestion_unread_count(request, channel_id):
    """
    GET   -> api/v2/suggestion/count_unread/              = get unread suggestion count in all channels
    GET   -> api/v2/suggestion/count_unread/<channel_id>/ = get unread suggestion count in a channel
    """
    if request.user.is_anonymous():
        raise PermissionDenied
    if channel_id:
        channel = get_object_or_404(CuratorChannel, pk=channel_id)
        if channel.user != request.user:
            raise PermissionDenied
        return Response({'count': channel.suggested_links.filter(is_read=False).count()})
    else:
        suggestion = CuratorSuggestedLink.objects.filter(is_read=False, channel__user=request.user)
        suggestion_by_channel = suggestion.values('channel').annotate(count=Count('channel'))
        return Response({
            'count': suggestion.count(),
            'by_channel': suggestion_by_channel
        })


class APIv2UserSuggestionView(APIView):
    """
    get and create a suggestion link
    GET    -> api/v2/suggestion/              = get all suggests for current user grouped by channel
    GET    -> api/v2/suggestion/<channel_id>/ = get specific channel (need owner permission)
    POST   -> api/v2/suggestion/<channel_id>/ = post new suggestion to other user channel

    post parameter
    'url'    URL  url of suggested video
    'detail' TEXT detail of video to post in channel
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsChannelOwner)

    def get(self, request, channel_id=None):
        if channel_id:
            channel = get_object_or_404(CuratorChannel, pk=channel_id)
            self.check_object_permissions(request, channel)
            suggestions = channel.suggested_links.filter(is_done=False)
            serializer = CuratorSuggestedLinkSerializer(suggestions, many=True)
            ret = serializer.data
            suggestions.update(is_read=True)
            return Response(ret)
        else:
            self.check_permissions(request)
            channels = request.user.curatorchannel_set.select_related('suggested_links').all()
            serializer = CuratorChannelSuggestedLinkSerializer(channels, many=True)
            ret = serializer.data
            for channel in channels:
                channel.suggested_links.update(is_read=True)
            return Response(ret)

    def post(self, request, channel_id=None):
        channel = get_object_or_404(CuratorChannel, pk=channel_id)
        self.check_permissions(request)  # check only user logged in
        try:
            serializer = CuratorSuggestedLinkSerializer(
                CuratorSuggestedLink(channel=channel, suggested_by=request.user),
                data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except (LookupError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(True, status=status.HTTP_201_CREATED)


class APIv2UserSuggestionActionView(APIView):
    """
    view, edit, approve, disapprove a suggestion
    GET  -> api/v2/suggestion/view/<suggestion_id>/       = get info of suggestion
    POST -> api/v2/suggestion/edit/<suggestion_id>/       = edit suggestion
    POST -> api/v2/suggestion/approve/<suggestion_id>/    = approve suggestion and create playlist
    POST -> api/v2/suggestion/disapprove/<suggestion_id>/ = disapprove suggestion and remove from list

    post parameter (for edit only)
    'url'    URL  url of suggested video
    'detail' TEXT detail of video to post in channel
    """

    permission_classes = (permissions.IsAuthenticated, IsSuggestedChannelOwner)

    def get(self, request, action, suggestion_id):
        if action != 'view':
            raise Http404
        suggestion = get_object_or_404(CuratorSuggestedLink, pk=suggestion_id)
        serializer = CuratorSuggestedLinkSerializer(suggestion)
        ret = serializer.data
        suggestion.read()
        return Response(ret)

    def post(self, request, action, suggestion_id):
        suggestion = get_object_or_404(CuratorSuggestedLink, pk=suggestion_id)
        self.check_object_permissions(request, suggestion)
        # print action
        if action == 'edit':
            try:
                serializer = CuratorSuggestedLinkSerializer(suggestion, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            except (LookupError, ValueError) as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif action == 'approve':
            playlist = suggestion.create_playlist()
            return Response(CuratorPlaylistLinkSerializer(playlist).data, status=status.HTTP_201_CREATED)
        elif action == 'disapprove':
            suggestion.done()
            # remember not to suggest again if come from auto system
            u = CuratorChannel.objects.get(id=settings.STAFF_PICK_CHANNEL).user
            if suggestion.suggested_by == u:
                CuratorUserUnwantedLink.objects.get_or_create(channel=suggestion.channel, link=suggestion.link)
            return Response(True, status=status.HTTP_202_ACCEPTED)
        raise Http404


# ============ Search ============= #

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_search_playlist(request):
    """
    GET -> api/v2/search/?q=Text = get search result for Text

    GET parameters
    'q'                   TEXT  search text
    'page'                INT   lookup page
    'per_page'            INT   results per page
    'save_history'        BOOL  save to search history, use with `api/v2/search_history/`
    'add_youtube_result'  BOOL  add search results from youtube
    'channel_id'          LIST  list of channel id
    """
    q = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    save_history = request.GET.get('save_history', False)
    add_youtube_result = request.GET.get('add_youtube_result', False)
    channel_id = request.GET.getlist('channel', [])
    # save search history
    if save_history and q != '':
        history = SearchHistory.objects.get_or_create_new_keyword(q, request.user)
        history.adjustHits(1)

    q_tokens = list(set(re.sub('\s+', ' ', q).strip().split(' ')))
    name_q = reduce(operator.and_, (Q(name__icontains=x) for x in q_tokens))
    channel_name_q = reduce(operator.and_, (Q(channel__name__icontains=x) for x in q_tokens))

    playlists = (CuratorPlaylist.objects.filter(Q(channel__access_level=AccessLevel.ANY,
                                                  sub_access_level=AccessLevel.ANY) & (name_q | channel_name_q))
                 .exclude(Q(channel__user_save=True) | Q(channel__isPrivate=True))
                 .prefetch_related('user_like', 'channel__user__userprofile')
                 .select_related('channel', 'link').order_by('-create_at'))
    if channel_id:
        playlists = playlists.filter(channel_id__in=channel_id)

    paginator = Paginator(playlists, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)
    serializer = CuratorPlaylistLinkSerializer(page_contents, many=True, context={'request': request})
    result = serializer.data
    # result from youtube
    if add_youtube_result and len(result) < int(per_page):
        search_query = dict(
            q=q,
            type='video',
            part='snippet',
            maxResults = int(per_page)-len(result)
        )
        search_response = youtube.search().list(**search_query).execute()
        youtube_result = []
        videos = []
        channels = []
        # get videos id
        for item in search_response.get("items", []):
            videos.append(item['id']['videoId'])
            channels.append(item['snippet']['channelId'])
        channel_query = dict(
            part=','.join(['snippet']),
            id=','.join(set(channels))
        )
        channels_image = {}
        channel_response = youtube.channels().list(**channel_query).execute()
        for item in channel_response.get("items", []):
            channels_image[item['id']] = item['snippet']['thumbnails']['default']['url']
        video_query = dict(
            part=','.join(['snippet', 'contentDetails']),
            id=','.join(videos)
        )
        video_response = youtube.videos().list(**video_query).execute()
        for item in video_response.get("items", []):
            desc = item['snippet']['description']
            row = {
                'id': '',
                'name': item['snippet']['title'],
                'channel': '',
                'channel_name': item['snippet']['channelTitle'],
                'search_source': 'youtube',
                'link': {
                    'real_thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'duration_s': int(isodate.parse_duration(item['contentDetails']['duration']).total_seconds()),
                    'url': "https://www.youtube.com/watch?v="+item['id']
                },
                'channel_image': channels_image.get(item['snippet']['channelId'], ''),
                'create_at': item['snippet']['publishedAt'],
                'detail': desc[:100]+'...' if len(desc) > 100 else desc,
                'src': VideoType.YOUTUBE,
                'src_id': item['id']
            }
            youtube_result.append(row)
        result.extend(youtube_result)

    return Response({'search_text': q,
                     'playlists': result,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_search_channel(request):
    """
    GET -> api/v2/search_channel/?q=Text = get search result for Text
    """
    q = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 40)
    q_tokens = list(set(re.sub('\s+', ' ', q).strip().split(' ')))
    channel_name_q = reduce(operator.and_, (Q(name__icontains=x) for x in q_tokens))
    channels = CuratorChannel.objects.filter(Q(access_level=AccessLevel.ANY) & channel_name_q,
                                             is_sqool=False, user_save=False).order_by('name')
    paginator = Paginator(channels, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)

    serializer = CuratorChannelSerializer(page_contents, many=True, context={'request': request})
    result = serializer.data

    return Response({'search_text': q,
                     'channels': result,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_search_r2(request):
    """
    GET -> api/v2/search/?q=Text

    get search result for Text
    return PentaChannel and Youtube as Playlist
    no PentaPlaylist returned
    """

    q = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 40))
    save_history = request.GET.get('save_history', True)
    add_youtube_result = request.GET.get('add_youtube_result', True)
    # save search history
    if save_history and q != '':
        history = SearchHistory.objects.get_or_create_new_keyword(q, request.user)
        history.adjustHits(1)

    q_tokens = list(set(re.sub('\s+', ' ', q).strip().split(' ')))
    channel_name_q = reduce(operator.and_, (Q(name__icontains=x) for x in q_tokens))
    channels = CuratorChannel.objects.filter(Q(access_level=AccessLevel.ANY) & channel_name_q,
                                             is_sqool=False, user_save=False).order_by('-rank_score', 'id')
    paginator = Paginator(channels, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)

    serializer = CuratorChannelSerializer(page_contents, many=True, context={'request': request})
    channel_result = serializer.data

    # result from youtube
    youtube_result = []
    if add_youtube_result:
        search_query = dict(
            q=q,
            type='video',
            part='snippet',
            maxResults=50
        )
        search_response = youtube.search().list(**search_query).execute()
        youtube_result = []
        videos = []
        channels = []
        # get videos id
        for item in search_response.get("items", []):
            videos.append(item['id']['videoId'])
            channels.append(item['snippet']['channelId'])
        channel_query = dict(
            part=','.join(['snippet']),
            id=','.join(set(channels))
        )
        channels_image = {}
        channel_response = youtube.channels().list(**channel_query).execute()
        for item in channel_response.get("items", []):
            channels_image[item['id']] = item['snippet']['thumbnails']['default']['url']
        video_query = dict(
            part=','.join(['snippet', 'contentDetails']),
            id=','.join(videos)
        )
        video_response = youtube.videos().list(**video_query).execute()
        for item in video_response.get("items", []):
            desc = item['snippet']['description']
            row = {
                'id': '',
                'name': item['snippet']['title'],
                'channel': '',
                'channel_name': item['snippet']['channelTitle'],
                'search_source': 'youtube',
                'link': {
                    'real_thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'duration_s': int(isodate.parse_duration(item['contentDetails']['duration']).total_seconds())
                },
                'channel_image': channels_image.get(item['snippet']['channelId'], ''),
                'create_at': item['snippet']['publishedAt'],
                'detail': desc,
                'src': VideoType.YOUTUBE,
                'src_id': item['id']
            }
            youtube_result.append(row)

    return Response({'search_text': q,
                     'channels': channel_result,
                     'playlists': youtube_result,
                     'has_other_pages': page_contents.has_other_pages(),
                     'page': page_contents.number,
                     'num_page': paginator.num_pages})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_get_search_history(request):
    if request.user.is_anonymous:
        raise PermissionDenied
    history = SearchHistory.objects.get_user_history(request.user)
    data = []
    for h in history:
        data.append(h.keyword)
    return Response(data)


# ============ Topic ============= #

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def api_v2_hottopic(request):
    """ get hot topics from google"""
    result = []
    now = datetime.now()
    last_result = cache.get('hottopic')
    last_sync = cache.get('hottopic_last_sync')
    if (not last_result) or (not last_sync) or (last_sync+timedelta(minutes=10)) <= now:
        result = [] # this does not work as of now AS Google always return 503
        # url = 'http://www.google.com/trends/hottrends/hotItems'
        # values = { 'ajax' : 1, 'pn' : 'p33', 'htv' : 'l' }
        # data = urllib.urlencode(values)
        # req = urllib2.Request(url, data)
        # response = urllib2.urlopen(req)
        # topics = json.loads(response.read())
        # staff_pick_channel = CuratorChannel.objects.filter(id=settings.STAFF_PICK_CHANNEL).first()
        # if not staff_pick_channel:
        #     raise APIException("not found staff pick channel")
        # user = staff_pick_channel.user
        # for t in topics['trendsByDateList']:
        #     for ts in t['trendsList']:
        #         title = ts['title']
        #         if any(ban_word in title for ban_word in settings.BANNED_KEYWORDS):
        #             continue
        #         ch, created = CuratorChannel.objects.get_or_create(name=title, is_create_from_auto=True, user=user)
        #         must_refresh = False
        #         if created:
        #             if 'imgUrl' in ts:
        #                 ch.icon_url = 'http:'+ts['imgUrl']
        #                 ch.save()
        #             mirror, created = CuratorMirror.objects.get_or_create(channel=ch)
        #             CuratorMirrorRule.objects.create(mirror=mirror, keyword=title, rule=CuratorMirrorRule.INCLUDE_RULE)
        #             must_refresh = True
        #         else:
        #             mirror, created = CuratorMirror.objects.get_or_create(channel=ch)
        #             if mirror.latest_sync <= hour4earlier():
        #                 mirror.active = True
        #                 mirror.save()
        #                 must_refresh = True
        #         if must_refresh:
        #             busy_key = 'hottopic_%d' % ch.id
        #             if not cache.get(busy_key):
        #                 cache.set(busy_key, True)
        #                 if is_worker_exists():
        #                     get_new_video_from_auto.delay(ch.id, deactive_on_finish=True)
        #                 else:
        #                     get_new_video_from_auto(ch.id, deactive_on_finish=True)
        #         result.append({'text': title, 'weight': ts['hotnessLevel'], 'link': ch.url() })
        # cache.set('hottopic', result)
        # cache.set('hottopic_last_sync', datetime.now())
    else:
        result = last_result
    return Response(result)


def fetch_hot_shared(world=False):
    result = {'playlists' : []}
    # url = 'http://www.youtube.com/trendsdashboard_ajax?action_feed_videos=1&feed=shared'
    # if not world:
    #     url += '&loc=tha'
    # req = urllib2.Request(url)
    # response = urllib2.urlopen(req)
    # vids = json.loads(response.read().replace('\U', 'U'))
    # soup = BeautifulSoup(vids.get('html_content', ''), "html.parser")
    # items = soup.findAll('div', {'class':'video-item'})
    exists_id = []
    # for t in items:
    #     id = t.attrs['alt']
    #     title = t.find('h4').text
    #     exists_id.append(id)
    #     if any(ban_word in title for ban_word in settings.BANNED_KEYWORDS):
    #         continue
    # from youtube trends
    videos = my_youtube.get_trend_videos(country_code=(None if world else 'TH'))
    for v in videos.get("items", []):
        id = v["id"]
        if id in exists_id:
            continue
        exists_id.append(id)
    vid_ref = my_youtube.get_youtube_video_info(exists_id, part='snippet,statistics', fields='items/id,items/snippet/title,items/statistics/likeCount,items/statistics/dislikeCount')
    for id in exists_id:
        ref = vid_ref.get(id)
        if ref:
            # print ref
            title = ref.get("snippet", {}).get("title", "")
            title_norm = title.lower()
            like = int(ref.get("statistics", {}).get("likeCount", 1))
            if like == 0:
                like = 1
            dislike = int(ref.get("statistics", {}).get("dislikeCount", 0))
            score = dislike*100.0/like
            # you might adjust value from 20 to value between 0 to 100+ (some vids have enormous dislikes)
            if score > 20:
                # print u"{3} {4} {1}/{0} {2:.2f}".format(like, dislike, dislike*100.0/like, id, title)
                continue
            # ban bad title and description
            if any(ban_word in title_norm for ban_word in settings.BANNED_KEYWORDS):
                continue
            result['playlists'].append({
                'id': id,
                'name': title,
                'detail': '',
                'link': {
                    'real_thumbnail': ('http://img.youtube.com/vi/%s/0.jpg' % id),
                    'video_id': id,
                    'video_type': VideoType.YOUTUBE
                },
            })
    return result


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def api_v2_hotshared(request):
    """ get hot shared from youtube"""
    world = json.loads(request.POST.get('world', "false"))
    now = datetime.now()
    data_key = 'hotshared_world' if world else 'hotshared'
    stamp_key = 'hotshared_world_last_sync' if world else 'hotshared_last_sync'
    last_result = cache.get(data_key)
    last_sync = cache.get(stamp_key)
    if (not last_result) or (not last_sync) or (last_sync+timedelta(minutes=60)) <= now:
        result = fetch_hot_shared(world=world)
        if len(result) > 0:
            cache.set(data_key, result)
            cache.set(stamp_key, datetime.now())
    else:
        result = last_result
    return Response(result)

# ============ Email ============= #

class APIv2EmailView(APIView):
    """
    get/edit/delete email

    GET    -> /api/v2/email/            = get all email
    GET    -> /api/v2/email/<email_id>/ = get email
    POST   -> /api/v2/email/<email_id>/ = edit
    DELETE -> /api/v2/email/<email_id>/ = delete

    Post parameters
      'subject'    STRING  subject of email
      'email'      EMAIL   email of sender, if null, email will be fill with user registered email
      'message'    TEXT    email message
      'playlist'   INT     video playlist id to attach
      'template'   INT     chosen template's id
      'video_position' INT position of video
      'image'    [INT, ..] list of image
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, email_id=None):
        if email_id is None:
            emails = FeedEmail.objects.filter(user=request.user).exclude(state=FeedEmail.STATE.deleted)
            return Response(FeedEmailSummarySerializer(emails, many=True).data)
        else:
            email = get_object_or_404(FeedEmail, id=email_id, user=request.user)
            return Response(FeedEmailFullDetailSerializer(email).data)

    def post(self, request, email_id=None):
        email = get_object_or_404(FeedEmail, id=email_id)
        if not has_edit_channel_permission(request.user, email.channel):
            raise PermissionDenied
        serializer = FeedEmailSerializer(email, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, email_id):
        email = get_object_or_404(FeedEmail, id=email_id)
        if not has_edit_channel_permission(request.user, email.channel):
            raise PermissionDenied
        email.state = FeedEmail.STATE.deleted
        email.save()
        return Response(True, status=status.HTTP_202_ACCEPTED)


class APIv2EmailChannelView(APIView):
    """
    get/create

    GET   -> /api/v2/email/channel/<channel_id> = get all email of specific channel
    POST  -> /api/v2/email/channel/<channel_id> = create

    Post parameters
      'subject'  STRING  subject of email
      'email'    EMAIL   email of sender, if null, email will be fill with user registered email
      'message'  TEXT    email message
      'playlist' INT     video playlist id to attach
    """
    permission_classes = (IsChannelOwner, )

    def get(self, request, channel_id):
        channel = get_object_or_404(CuratorChannel, id=channel_id)
        self.check_object_permissions(request, channel)
        emails = FeedEmail.objects.filter(channel=channel).exclude(state=FeedEmail.STATE.deleted)
        return Response(FeedEmailSummarySerializer(emails, many=True).data)

    def post(self, request, channel_id):
        channel = get_object_or_404(CuratorChannel, id=channel_id)
        self.check_object_permissions(request, channel)
        serializer = FeedEmailSerializer(FeedEmail(channel=channel, user=request.user), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def api_v2_email_upload_image(request, email_id):
    """
    upload image for email

    Post parameters
      'image'    IMAGE image to upload
      'position' INT   position of image on template (begin with 0 to n-1)
    """
    if request.user.is_anonymous():
        raise PermissionDenied
    email = get_object_or_404(FeedEmail, id=email_id)
    serializer = FeedEmailImageSerializer(FeedEmailImage(email=email), data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def api_v2_email_send(request, email_id):
    email = get_object_or_404(FeedEmail, id=email_id)
    if request.user != email.user:
        raise PermissionDenied
    try:
        if email.send(request):
            return Response(True, status=status.HTTP_202_ACCEPTED)
    except ValueError as e:
        return Response({'detail': e}, status=status.HTTP_400_BAD_REQUEST)
    return Response(False, status=status.HTTP_406_NOT_ACCEPTABLE)


class APIv2EmailTemplateView(APIView):
    """
    get email template
    """

    def get(self, request, template_id=None):
        if template_id is None:
            templates = FeedEmailTemplate.objects.all()
            return Response(FeedEmailTemplateSerializer(templates, many=True).data)
        else:
            template = get_object_or_404(FeedEmailTemplate, id=template_id)
            return Response(FeedEmailTemplateSerializer(template).data)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def api_v2_account_create(request):
    """
    Create new account

    Post parameters
      'email'    EMAIL    email of new account
      'password' PASSWORD password for new account
      'fullname' STRING   fullname of new account, will be split to first/last name using ' ' as delimiter
    """
    try:
        email = request.data['email']
        password = request.data['password']
        fullname = request.data['fullname']
    except KeyError as e:
        return Response({'detail': 'Need %s' % e}, status=status.HTTP_400_BAD_REQUEST)
    first_name, last_name = fullname.strip().rsplit(' ', 1)
    api = AccountAPI()
    ret, message = api.create_user(email, password, first_name, last_name)
    if ret:
        return Response({'detail': message}, status=status.HTTP_201_CREATED)
    else:
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


def safe_equal(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def hmac_sha256(secret, message):
    """Return HMAC_SHA256(secret, message)"""
    # Compatible with Python2 and Python3
    hash = base64.urlsafe_b64encode(hmac.new(secret, message, hashlib.sha256).digest())
    return hash


class APIv2CreateGuestView(APIView):  # PREVENT
    authentication_classes = []
    permission_classes = []

    # permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def post(self, request):
        try:
            unique_id = request.data['unique_id']
            time = request.data['time']
            hkey = request.data['hkey']
            device_type = request.data['device_type']
        except KeyError as e:
            return Response({'detail': 'Need \'%s\'' % e}, status=status.HTTP_400_BAD_REQUEST)

        message = str(unique_id) + str(time)
        message = message.encode("utf8")
        calculated_hkey = hmac_sha256(S_KEY, message)
        is_equal_hash_chk = safe_equal(hkey , calculated_hkey.decode("utf8"))

        if not is_equal_hash_chk:
            return Response({'detail': "hkey validation failed."}, status=status.HTTP_400_BAD_REQUEST)

        api = AccountAPI()
        ret, message = api.create_guest_user(unique_id, time, device_type)  # Get token with UNIQUE ID

        if ret:
            # Create user success full message is token key
            return Response({'token': message}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


class APIv2CreateFBView(APIView):
    """
        Create new account with Facebook Token
        example Json
        {
            'fb_token':{
                'access_token':'XXXXXXXXX',
                'id':'fb00000000',
                'expires':'XXXXX',
            } ,
            'fb_infos':{
                'username':'AAA',
                'firstname':'BBB',
                'lastname':'CCC',
                'email':'DDD',
                'avatarurl':'http://xxx.yy.zz',
            }
        }
    """
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def post(self, request):
        try:
            fb_token = request.data['fb_token']
            fb_infos = request.data['fb_infos']
            unique_id = request.data['unique_id']
            time = ''  # request.data['time']
            hkey = ''  # request.data['hkey']
            device_type = request.data['device_type']
            device_token = request.data['device_token']
            app = request.data.get('app')
        except KeyError as e:
            return Response({'detail': 'Need \'%s\'' % str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # calculated_hkey = hmac_sha256(S_KEY, str(unique_id) + str(time))
        # is_equal_hash_chk = safe_equal(hkey , calculated_hkey)
        # if not is_equal_hash_chk:
        #     return Response({'detail': "hkey validation failed."}, status=status.HTTP_400_BAD_REQUEST)

        pUser = None
        # Authenthication pass
        # if not request.user.is_anonymous():
        #     pUser = request.user
        # else:
        #     pUser = None

        try:
            access_token = fb_token['access_token']
            fb_id = fb_token['id']
            # fb_expire = fb_token['expires']
            fb_expire = None
        except KeyError as e:
            return Response({'Malformed Facebook Token': 'Need \'%s\'' % str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fb_username = fb_infos['username']
            fb_firstname = fb_infos['firstname']
            fb_lastname = fb_infos['lastname']
            fb_email = fb_infos['email']
            fb_avatarUrl = fb_infos['avatarurl']
        except KeyError as e:
            return Response({'Malformed Facebook Info': 'Need \'%s\'' % str(e)}, status=status.HTTP_400_BAD_REQUEST)

        api = AccountAPI()
        ret, message = api.create_facebook_user(
            access_token, unique_id, time, device_type, fb_id, fb_username, fb_firstname,  fb_lastname,
            fb_email, fb_avatarUrl, fb_expire, pUser, device_token, app
        )

        tmp = APIToken.objects.get(key=message)
        if ret:
            # Create user success full message is token key
            return Response(
                {
                    'token': message,
                    "profile": {
                        "userId": int(tmp.user.id),
                        "username": fb_username,
                        "lastname": fb_lastname,
                        "image": fb_avatarUrl,
                        "fullname": fb_firstname,
                        "email": fb_email
                    }
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def api_v2_account_login(request):
    """
    login

    Post parameters
    ---------------
    -'email'        EMAIL    email of user
    -'password'     PASSWORD password of user
    -'from_url'     URL      url to return after login (default: / )
    -'device_type'  STRING
    -'device_token' STRING   device token
    -'unique_id'    STRING   device unique id
    -'app'          STRING   application name
    """
    try:
        email = request.data['email']
        password = request.data['password']
        device_type = request.data.get('device_type', 'etc')
        device_token = request.data.get('device_token', '')
        device_id = request.data.get('unique_id', '0')
        from_url = request.data.get('from_url', request.get_host())
        app = request.data.get('app', None)
    except KeyError as e:
        return Response({'detail': 'Need %s' % e}, status=status.HTTP_400_BAD_REQUEST)
    api = AccountAPI()
    ret, message = api.login(from_url, email, password)
    if ret:
        # gen authToken
        user, userCreated = User.objects.get_or_create(username=email.replace("@","-"))
        if userCreated:
            user.set_password(password)
            user.save()

        profile = {
            'id': user.id,
            'username': user.username,
            'fullname': user.first_name,
            'lastname': user.last_name,
            'email': user.email,
            'image': ''
        }
        tmp = UserProfile.objects.filter(user=user)
        if tmp:
            try:
                profile['image'] = tmp[0].image.path[tmp[0].image.path.find('media'):]
            except NotImplementedError:
                profile['image'] = tmp[0].image.url

        with transaction.atomic():
            device_type = MobileDevice.Type.get(device_type)
            device, __ = MobileDevice.objects.get_or_create(user=user, device_id=device_id,
                                                            device_type=device_type)
            device.device_name = '{}-{}'.format(device_type, device_id)
            device.device_token = device_token
            device.save()

        token = device.get_token()

        if app:
            application_default_role, __ = ApplicationDefaultRole.objects.get_or_create(name=app.lower())
        else:
            application_default_role = ApplicationDefaultRole.objects.get_default()
        application_default_role.apply_role_to_user(user)

        return Response({'token': token.key, 'profile': profile})
    else:
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def api_v2_account_logout(request):
    if request.user.is_anonymous():
        return Response({'detail': 'Not login yet'}, status=status.HTTP_403_FORBIDDEN)
    try:
        device_token = request.data.get('device_token', '')
        if device_token:
            MobileDevice.objects.filter(device_token=device_token).update(device_token='')
        return Response({'result': 'success'})
    except Exception as e:
        logger.warning(device_token + " device_token delete error")
        logger.exception(e)
    return Response({'url': '/accounts/logout/'})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_account_update_visit_follow_page(request):
    if not request.user.is_anonymous():
        userprofile = request.user.userprofile
        userprofile.last_visit_follow_page = timezone.now()
        userprofile.save()
        return Response(True)
    return Response(False)


# util
@api_view(['POST'])
def api_v2_util_video_description(request):
    url = request.data.get('url', None)
    desc = CuratorLink.objects.get_video_description_from_url(url)
    return Response(desc)


class AccountMostContributer(APIView):
    authentication_classes = []
    permission_classes = []
    @cache_response(60*60) # 1 hour
    def get(self, request):
        amount = int(request.GET.get('amount', 10))
        ids = (CuratorChannel.objects.filter(access_level=AccessLevel.ANY, isPrivate=False,
                                             user_share=False, is_create_from_auto=False,
                                             user__is_staff=False)
               .exclude(curatorplaylist=None).values_list('user', flat=True)
               .annotate(c=Count('user')).order_by('-c')[:amount])
        result = []
        for id in ids:
            u = User.objects.filter(id=id).first()
            if u:
                try: tmp = u.userprofile.real_image()
                except: tmp = ""
                data = {
                    'name': u.first_name,
                    'picture': tmp
                }
                result.append(data)
        return Response(result)


class AccountProfilePictureAPIView(APIView):
    parser_classes = (ImageUploadParser, MultiPartParser)

    def post(self, request):
        logger.debug("upload profile picture")
        if not request.user.is_authenticated:
            raise PermissionDenied
        user = request.user
        file_obj = request.data['file']
        logger.debug(file_obj.content_type)
        if not file_obj.content_type.startswith('image'):
            return Response({'detail': 'content type not support'},
                            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        img = Image.open(file_obj.file)
        converted_img = BytesIO()
        img = img.resize((200, 200), Image.ANTIALIAS)
        img.save(converted_img, format='JPEG', quality=100)
        converted_img.seek(0)
        user.userprofile.image.save("%s.jpg" % uuid4(), File(converted_img))
        logger.debug(user.userprofile.real_image())
        # print(user.userprofile.real_image())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        user = request.user
        if not user.is_authenticated or user.userprofile is None:
            raise Http404()
        return Response({'real_image': user.userprofile.real_image()})


# Question -----------------------------------------------------------------------------------------------
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_question_list_message(request, playlist_id):
    user = request.user
    if user.is_anonymous():
        raise PermissionDenied
    if not playlist_id:
        raise APIException("no playlist specific")
    playlist = CuratorPlaylist.objects.filter(id=playlist_id).first()
    if not playlist:
        raise APIException("target playlist not found")
    questioner_id = None
    if user == playlist.channel.user:
        questioner_id = request.GET.get('from', None)
    else:
        questioner_id = user.id
    if questioner_id == None:
        raise APIException("not found who question")
    forum = QuestionForum.objects.filter(playlist=playlist, questioner_id=questioner_id).first()
    if not forum:
        return Response([])
    ret = {}
    all_message = (QuestionThread.objects.filter(questionforum=forum)
                   .select_related('suggestplaylistfromquestion').order_by('-created'))
    timestamp = timezone.now()
    channel_avatar = playlist.channel.real_icon()
    questioner_avatar = forum.questioner.userprofile.real_image()
    is_questioner = user == forum.questioner
    questioner_id = forum.questioner.id
    ret['message'] = []
    for r in all_message:
        data = {
            'id': r.id,
            'message': r.message,
            'created': r.created,
            'created_by_id': r.created_by.id,
            'avatar': questioner_avatar if r.created_by.id == questioner_id else channel_avatar,
            'isNew': (forum.last_view_by_questioner < r.created if is_questioner
                      else forum.last_view_by_owner < r.created),
            'suggest': []
        }
        all_suggestion = r.suggestplaylistfromquestion_set.order_by('-created')
        for s in all_suggestion:
            sdata = {
                'id': s.id,
                'name': s.playlist.name,
                'link': s.playlist.url()
            }
            data['suggest'].append(sdata)
        ret['message'].append(data)
    if is_questioner:
        forum.last_view_by_questioner = timestamp
    else:
        forum.last_view_by_owner = timestamp
    forum.save()
    return Response(ret)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_v2_question_list_questioner(request, playlist_id):
    user = request.user
    if user.is_anonymous() or not user.email in SUPER_ADMIN_LIST:
        raise PermissionDenied
    if not playlist_id:
        raise APIException("no playlist specific")
    playlist = CuratorPlaylist.objects.filter(id=playlist_id).first()
    if not playlist:
        raise APIException("target playlist not found")
    # if playlist.channel.user != user:
    #     raise PermissionDenied
    forums = (QuestionForum.objects.filter(playlist=playlist)
              .select_related('questioner').order_by('-updated_by_questioner'))
    ret = {'questioner': []}
    avatar_cache = {}
    for f in forums:
        last_view = f.last_view_by_owner if f.last_view_by_owner else '1970-01-01T00:00:00Z'
        avatar = f.questioner.userprofile.real_image()
        avatar_cache[f.questioner.id] = avatar
        data = {
            'id': f.questioner.id,
            'name': f.questioner.first_name,
            'c_unread': f.questionthread_set.filter(created__gt=last_view).exclude(created_by=user).count(),
            'avatar': avatar
        }
        ret['questioner'].append(data)
    threads = QuestionThread.objects.filter(questionforum__playlist=playlist).select_related('suggestplaylistfromquestion').exclude(created_by=user).order_by('-created')
    ret['message'] = []
    for t in threads:
        last_view_by_owner = t.questionforum.last_view_by_owner
        data = {
            'id': t.id,
            'message': t.message,
            'created': t.created,
            'created_by_id': t.created_by.id,
            'avatar': avatar_cache.get(t.created_by.id, ''),
            'isNew': t.created > last_view_by_owner if last_view_by_owner else True,
            'suggest': []
        }
        all_suggestion = t.suggestplaylistfromquestion_set.order_by('-created')
        for s in all_suggestion:
            sdata = {
                'id': s.id,
                'name': s.playlist.name,
                'link': s.playlist.url()
            }
            data['suggest'].append(sdata)
        ret['message'].append(data)
    forums.update(last_view_by_owner=timezone.now())
    return Response(ret)


@api_view(['POST'])
def api_v2_question_send_message(request, playlist_id):
    user = request.user
    if user.is_anonymous():
        raise PermissionDenied
    if not playlist_id:
        raise APIException("no playlist specific")
    msg = request.DATA.get('msg')
    if not msg:
        raise APIException("no message specific")
    playlist = CuratorPlaylist.objects.filter(id=playlist_id).first()
    if not playlist:
        raise APIException("target playlist not found")
    questioner = None
    if user == playlist.channel.user:
        questioner = User.objects.filter(id=request.DATA.get('questioner', None)).first()
    else:
        questioner = user
    if not questioner:
        raise APIException("not found who question")
    forum = QuestionForum.objects.filter(playlist=playlist, questioner=questioner).first()
    if not forum:
        if playlist.channel.user == user:
            raise APIException("owner cannot initial")
        forum = QuestionForum.objects.create(playlist=playlist, questioner=user)
    # check if before lastest reply must be within minute to prevent spam
    last_two_reply = forum.questionthread_set.order_by('-created')[:2]
    if len(last_two_reply) == 2:
        now = timezone.now()
        if last_two_reply[1].created + timedelta(minutes=1) >= now:
            raise APIException("must wait for a minute before you can send a message again")
    thread = QuestionThread.objects.create(questionforum=forum, created_by=user, message=msg)
    timestamp = thread.created
    ret = {}
    is_questioner = user == forum.questioner
    questioner_id = forum.questioner.id
    if is_questioner:
        forum.last_view_by_questioner = timestamp
        forum.updated_by_questioner = timestamp
    else:
        forum.updated_by_owner = timestamp
        forum.last_view_by_owner = timestamp
    forum.updated = timestamp
    forum.save()
    channel_avatar = playlist.channel.real_icon()
    questioner_avatar = forum.questioner.userprofile.real_image()
    all_message = QuestionThread.objects.filter(questionforum=forum).select_related('suggestplaylistfromquestion').order_by('-created')
    ret['message'] = []
    for r in all_message:
        data = {
            'id': r.id,
            'message': r.message,
            'created': r.created,
            'created_by_id': r.created_by.id,
            'avatar': questioner_avatar if questioner_id == r.created_by.id else channel_avatar,
            'isNew': (forum.last_view_by_questioner < r.created if is_questioner
                      else forum.last_view_by_owner < r.created),
            'suggest': [],
        }
        all_suggestion = r.suggestplaylistfromquestion_set.order_by('-created')
        for s in all_suggestion:
            sdata = {
                'id': s.id,
                'name': s.playlist.name,
                'link': s.playlist.url()
            }
            data['suggest'].append(sdata)
        ret['message'].append(data)
    return Response(ret)


@api_view(['POST'])
def api_v2_question_set_open(request, playlist_id):
    user = request.user
    if not user.email in SUPER_ADMIN_LIST:
        raise PermissionDenied
    if not playlist_id:
        raise APIException("no playlist specific")
    playlist = CuratorPlaylist.objects.filter(id=playlist_id).first()
    if not playlist:
        raise APIException("target playlist not found")
    want_open = request.DATA.get('want_open')
    if want_open == None:
        raise APIException("no status specific")
    if not hasattr(playlist, 'extra'):
        extra = CuratorPlaylistExtra.objects.create(playlist=playlist)
    playlist.extra.open_for_question = want_open
    playlist.extra.save()
    return Response(True)


@api_view(['POST'])
def api_v2_question_add_suggest_playlist(request, thread_id):
    user = request.user
    if user.is_anonymous() or not user.email in SUPER_ADMIN_LIST:
        raise PermissionDenied
    t = QuestionThread.objects.filter(id=thread_id).first()
    if not t:
        raise APIException("target thread not found")
    # if not t.questionforum.playlist.channel.user == user:
    #     raise APIException("only owner can suggest playlist")
    playlist_id = request.DATA.get('playlist_id')
    if not playlist_id:
        raise APIException("no playlist specific")
    playlist = CuratorPlaylist.objects.filter(id=playlist_id).first()
    if not playlist:
        raise APIException("target playlist not found")
    suggest, create = SuggestPlaylistFromQuestion.objects.get_or_create(questionthread=t, playlist=playlist)
    if not create:
        raise APIException("this playlist have been suggested before")
    all_suggestion = t.suggestplaylistfromquestion_set.order_by('-created')
    result = []
    for s in all_suggestion:
        data = {
            'name': s.playlist.name,
            'link': s.playlist.url()
        }
        result.append(data)
    return Response(result)


@api_view(['POST'])
def api_v2_question_remove_suggest_playlist(request, suggest_id):
    user = request.user
    if user.is_anonymous():
        raise PermissionDenied
    suggest = SuggestPlaylistFromQuestion.objects.filter(id=suggest_id).first()
    if not suggest:
        raise APIException("target suggest not found")
    if not suggest.questionthread.questionforum.playlist.channel.user == user:
        raise APIException("only owner can remove suggest")
    suggest.delete()
    return Response(True)

# -----------------------------------------------------------------------------------------------


# Chat ------------------------------------------------------------------------------------------

class APIv2ChatLiveView(APIView):
    def post(self, request):
        if request.user.is_anonymous():
            raise PermissionDenied
        live_id = request.DATA.get('live_id')
        msg = request.DATA.get('msg')
        if live_id and msg:
            message = [{
                'name': request.user.first_name,
                'avatar': request.build_absolute_uri(request.user.userprofile.real_image()),
                'message': msg
            }]
            pusher.chat_live(live_id, message)
            return Response(True)
        raise CustomAPIException("must specific id and/or message")

# -----------------------------------------------------------------------------------------------
