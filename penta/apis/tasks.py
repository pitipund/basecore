# -*- coding: utf-8 -*-

import isodate
import json
import re
import traceback

from his.penta.curator.models import CuratorChannel, CuratorLink, CuratorUserUnwantedLink, CuratorMirrorRule, CuratorMirror
from his.penta.curator.models import CuratorPlaylist, CuratorTag
from his.penta.curator.models import User
from his.penta.feed.models import CuratorSuggestedLink
from celery import shared_task
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Q
from django.db.models.aggregates import Count
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from his.penta.curator.serializers import CuratorLinkSummaryForRoomSerializer
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from apiclient.discovery import build
from his.penta.showtime.utils import VideoType, AccessLevel


@shared_task
def update_get_link_from_tag(username, tag_id, page, per_page, caching=True, ttl=settings.CACHE_TIMESPAN_IN_ROOM):
    mainGroup = []
    if tag_id == str(settings.TAG_POPULAR_ID):
        mainGroup = CuratorPlaylist.objects.filter(channel__access_level=AccessLevel.ANY, sub_access_level=AccessLevel.ANY).exclude(Q(channel__user_save=True)|Q(channel__isPrivate=True)).extra(select={'day': 'date(curator_curatorplaylist.create_at)'}).values('day', 'channel_id').annotate(c=Count('create_at')).order_by('-day', '-channel__rank_score')
    elif tag_id == str(settings.TAG_NEW_CHANNEL_ID):
        mainGroup = CuratorPlaylist.objects.filter(channel__access_level=AccessLevel.ANY, sub_access_level=AccessLevel.ANY).exclude(Q(channel__user_save=True)|Q(channel__isPrivate=True)).extra(select={'day': 'date(curator_curatorplaylist.create_at)'}).values('day', 'channel_id').annotate(c=Count('create_at')).order_by('-day', '-channel__create_at')
    else:
        mainGroup = CuratorPlaylist.objects.filter(Q(channel__access_level=AccessLevel.ANY, sub_access_level=AccessLevel.ANY)&(Q(tags=tag_id)|Q(channel__tags=tag_id))).exclude(Q(channel__user_save=True)|Q(channel__isPrivate=True)).extra(select={'day': 'date(curator_curatorplaylist.create_at)'}).values('day', 'channel_id').annotate(c=Count('create_at')).order_by('-create_at')
    paginator = Paginator(mainGroup, per_page)
    try:
        page_contents = paginator.page(page)
    except PageNotAnInteger:
        page_contents = paginator.page(1)
    except EmptyPage:
        page_contents = paginator.page(paginator.num_pages)
    result = []
    existsLinkInGroup = []
    user = User.objects.filter(username=username).first()
    if not user:
        user = AnonymousUser()
    plCache = {}
    for group in page_contents.object_list:
        # get playlists from channel group by date
        playlistInGroup = []
        if tag_id in [ str(settings.TAG_POPULAR_ID), str(settings.TAG_NEW_CHANNEL_ID) ]:
            playlistInGroup = CuratorPlaylist.objects.filter(sub_access_level=AccessLevel.ANY, channel=group['channel_id'], create_at__startswith=group['day']).select_related('link').order_by('-create_at')
        else:
            playlistInGroup = CuratorPlaylist.objects.filter(sub_access_level=AccessLevel.ANY, channel=group['channel_id'], create_at__startswith=group['day']).filter(Q(tags=tag_id)|Q(channel__tags=tag_id)).select_related('link').order_by('-create_at')
        existsLink = []
        links = []
        # get all links in each group
        for playlist in playlistInGroup:
            if not playlist.link_id in existsLink:
                serializer = CuratorLinkSummaryForRoomSerializer([playlist.link], many=True, context={'user': user, 'create_at': playlist.create_at, 'plCache': plCache})
                links.append(serializer.data[0])
                existsLink.append(playlist.link_id)
        links.reverse()
        # each group collapse extralink
        for l in links:
            if not l['id'] in existsLinkInGroup:
                finalLink = l
                links.remove(l)
                finalLink['extra_links'] = links
                existsLinkInGroup.append(l['id'])
                result.append(finalLink)
                break
    tag_name = None
    if result:
        tag = CuratorTag.objects.get(id=tag_id)
        tag_name = tag.name
    finalResult = {
        'tag': tag_name,
         'links': result,
         'has_other_pages': page_contents.has_other_pages(),
         'page': page_contents.number,
         'num_page': paginator.num_pages
    }
    if caching:
        key = 'get_link_tag_%s_%s_%s' % ( tag_id, page, per_page )
        busy_key = '%s_busy' % key
        # print("[save]", key)
        cache.set(key, (finalResult, datetime.now()+timedelta(seconds=ttl)), None)
        cache.set(busy_key, False)
    return finalResult


@shared_task
def get_new_video_from_auto(channel_id, deactive_on_finish=False, logger=None):
    limit_video = 400
    max_request = 50
    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_KEY)
    ch = CuratorChannel.objects.filter(id=channel_id).first()
    if logger:
        logger.debug(u'Get new video for channel {}'.format(ch.name))
    if not ch:
        return False
    busy_key = 'hottopic_%d' % ch.id
    now = datetime.utcnow()
    targetDate = now - timedelta(days=183)  # not older than half a year
    targetDateNormalized = targetDate.isoformat("T") + "Z"
    # now can have only one mirror
    mirror = CuratorMirror.objects.filter(channel=ch, active=True).first()
    if not mirror:
        cache.set(busy_key, False)
        return False
    playlist_id = None
    video_ids = []
    publish_after = mirror.must_publish_after if mirror.must_publish_after else None
    publish_before = mirror.must_publish_before if mirror.must_publish_before else None
    from_channel = False

    if mirror.youtube_playlist_id or mirror.youtube_channel_id or mirror.youtube_user_id:
        if mirror.youtube_playlist_id:
            playlist_id = mirror.youtube_playlist_id
        else:
            from_channel = True
            channel_query = dict(
                part='contentDetails',
                fields='items/contentDetails/relatedPlaylists/uploads'
            )
            if mirror.youtube_channel_id:
                channel_query['id'] = mirror.youtube_channel_id
            elif mirror.youtube_user_id:
                channel_query['forUsername'] = mirror.youtube_user_id
            else:
                cache.set(busy_key, False)
                return False
            channel_response = youtube.channels().list(**channel_query).execute()
            result = channel_response.get('items', [])
            if len(result) > 0:
                playlist_id = result[0]['contentDetails']['relatedPlaylists']['uploads']

        if not playlist_id:
            cache.set(busy_key, False)
            return False

        matcher = None
        rejecter = None
        if mirror.curatormirrorrule_set.count() > 0:
            match_keyword = []
            ban_keyword = []
            for r in mirror.curatormirrorrule_set.all():
                if r.rule == CuratorMirrorRule.INCLUDE_RULE:
                    match_keyword.append('(?=.*%s.*)' % r.keyword)
                else:
                    ban_keyword.append('.*%s.*' % r.keyword)
            if len(match_keyword) > 0:
                matcher = re.compile((''.join(match_keyword)), re.IGNORECASE)
            if len(ban_keyword) > 0:
                rejecter = re.compile(('|'.join(ban_keyword)), re.IGNORECASE)
        playlist_query = dict(
            playlistId=playlist_id,
            part='snippet',
            fields='nextPageToken,items/snippet/title,items/snippet/resourceId/videoId,items/snippet/publishedAt',
            maxResults=max_request,  # youtube max = 50
        )
        playlist_response = {}
        try:
            playlist_response = youtube.playlistItems().list(**playlist_query).execute()
        except Exception as e:
            if logger:
                logger.exception(e.message)
            content = json.loads(e.content)
            if 'error' in content:
                errorInfo = content['error']
                if errorInfo.get('code') == 404:
                    for error in errorInfo.get('errors', []):
                        if error.get('reason') == 'playlistNotFound':
                            if mirror.youtube_playlist_id:
                                mirror.youtube_playlist_id = ("%s (invalid)" % mirror.youtube_playlist_id)
                            mirror.active = False
                            mirror.save()
                            cache.set(busy_key, False)
                            # should notify owner by email or ui on website
                            return False

        should_stop = False
        while playlist_response and (len(video_ids) < (limit_video - max_request)):
            for item in playlist_response.get("items", []):
                title = item['snippet']['title']
                publish_date = isodate.parse_datetime(item['snippet']['publishedAt'])
                if matcher and not matcher.match(title):
                    continue
                if rejecter and rejecter.match(title):
                    continue
                if publish_after and publish_date < publish_after:
                    if from_channel:
                        should_stop = True
                        break
                    continue
                if publish_before and publish_date > publish_before:
                    continue
                video_ids.append(item['snippet']['resourceId']['videoId'])
            if should_stop:
                break
            next_page_token = playlist_response.get("nextPageToken", None)
            try:
                if next_page_token:
                    playlist_query['pageToken'] = next_page_token
                    playlist_response = youtube.playlistItems().list(**playlist_query).execute()
                else:
                    playlist_response = None
            except Exception as e:
                if logger:
                    logger.exception(e.message)
                playlist_response = None

    else:
        if mirror.curatormirrorrule_set.count() == 0:
            cache.set(busy_key, False)
            return False
        search_query = dict(
            type='video',
            part='snippet',
            fields='items/id/videoId',
            maxResults=10
        )
        if publish_after:
            search_query['publishedAfter'] = publish_after
        if publish_before:
            search_query['publishedBefore'] = publish_before
        if mirror.latest_first:
            search_query['order'] = 'date'
        else:
            search_query['order'] = 'relevance'
        query_string = []
        for con in mirror.curatormirrorrule_set.all():
            kw = con.keyword.strip()
            if con.rule == CuratorMirrorRule.INCLUDE_RULE:
                query_string.append(kw)
            else:
                words = kw.split(' ')
                query_string.extend([(u'-%s' % w) for w in words])
        search_query['q'] = ' '.join(query_string)
        # if more than 50, you need to do nextPageToken
        search_response = youtube.search().list(**search_query).execute()
        for item in search_response.get("items", []):
            video_ids.append(item['id']['videoId'])
    # print('total ids:', len(video_ids))

    # filter out exists link in channel
    exist_playlist = set(CuratorPlaylist.objects.filter(channel=ch, link__video_type=VideoType.YOUTUBE,
                                                        link__video_id__in=video_ids).values_list('link__video_id',
                                                                                                  flat=True))
    # filter out exists link in suggest
    exist_suggest = set(CuratorSuggestedLink.objects.filter(channel=ch, link__video_type=VideoType.YOUTUBE,
                                                            link__video_id__in=video_ids,
                                                            is_done=False).values_list('link__video_id', flat=True))
    # filter out user unwanted link in this channel
    unwant_ids = set(CuratorUserUnwantedLink.objects.filter(channel=ch, link__video_type=VideoType.YOUTUBE,
                                                            link__video_id__in=video_ids).values_list('link__video_id',
                                                                                                      flat=True))

    exclude_video_ids = exist_playlist.union(exist_suggest).union(unwant_ids)
    video_ids = [x for x in video_ids if x not in exclude_video_ids]

    # reduce request
    links_mapper = {}
    exist_link = CuratorLink.objects.filter(video_type=VideoType.YOUTUBE,
                                            video_id__in=video_ids).only('id', 'video_id')
    exist_link_ids = set()
    for l in exist_link:
        links_mapper[l.video_id] = l
        exist_link_ids.add(l.video_id)

    request_link = [x for x in video_ids if x not in exist_link]

    youtube_url = 'https://www.youtube.com/watch?v='
    # print 'new links', len(request_link)
    vid_chunks = [request_link[i:i+max_request] for i in range(0, len(request_link), max_request)]
    suggest_user = None

    if not mirror.instant_add:
        staff_channel = CuratorChannel.objects.get(id=settings.STAFF_PICK_CHANNEL)
        suggest_user = staff_channel.user

    with transaction.atomic():
        try:
            for chunk in vid_chunks:
                video_query = dict(
                    part=','.join(['snippet', 'contentDetails']),
                    id=','.join(chunk),
                    fields='items/id,items/snippet/title,items/snippet/channelId,'
                           'items/snippet/channelTitle,items/snippet/description,'
                           'items/snippet/publishedAt,items/contentDetails/duration,'
                           'items/contentDetails/regionRestriction/blocked'
                )
                video_response = youtube.videos().list(**video_query).execute()
                for v in video_response.get("items", []):
                    # check if video is blocked, by the way don't want to put in curatorunwantedlink
                    if "TH" in v["contentDetails"].get("regionRestriction", {}).get("blocked", []):
                        video_ids.remove(v['id'])
                        continue
                    name = v['snippet']['title']
                    url = youtube_url + v['id']
                    duration = int(isodate.parse_duration(v['contentDetails']['duration']).total_seconds())
                    video_type = VideoType.YOUTUBE
                    video_id = v['id']
                    thumbnail_url = "http://img.youtube.com/vi/" + v['id'] + "/0.jpg"
                    payload = v['snippet']['description']
                    provider_id = v['snippet']['channelId']
                    provider_name = v['snippet'].get('channelTitle', '')
                    publish = isodate.parse_datetime(v['snippet']['publishedAt'])
                    l = CuratorLink.objects.create(name=name, url=url, duration_s=duration,
                                                   video_type=video_type, video_id=video_id,
                                                   provider_id=provider_id, provider_name=provider_name,
                                                   thumbnail_url=thumbnail_url, payload=payload,
                                                   published_at=publish)
                    links_mapper[video_id] = l
            # create playlist
            video_ids.reverse()
            if len(video_ids) <= 9:
                video_ids = reorderPart(video_ids, links_mapper)
            for vid in video_ids:
                if vid in links_mapper:
                    l = links_mapper[vid]
                    if mirror.instant_add:
                        l.create_new_playlist(ch, from_rules_auto=True)
                    else:
                        CuratorSuggestedLink.objects.create(channel=ch, link=l, suggested_by=suggest_user)
            # transaction.commit()
        except Exception as e:
            # print e
            if logger:
                logger.exception(e)

    mirror.latest_sync = timezone.now()
    if deactive_on_finish:
        mirror.active = False
    mirror.save()
    if ch.auto_sort:
        ch.sort_videos_by_pattern()
    cache.set(busy_key, False)
    return True


PATTERN = ['.*\D*(\d+)/(\d+)\D*.*']
MATCHER = re.compile('|'.join(PATTERN), re.IGNORECASE)


def reorderPart(video_ids, links_mapper):
    """
    try to reorder episode when it split to multiple parts
    match pattern with x/y group by same day (may cause bug if parts were upload in the midnight)
    assume that videos_ids already have chronological order
    """
    reordered_video_ids = []
    stall = []
    current_stall_total = None
    current_stall_timestamp = None
    for vid in video_ids:
        if not vid in links_mapper:
            continue
        l = links_mapper[vid]
        l_match = MATCHER.match(l.name)
        if l_match:
            idx, total = l_match.groups()
            if not current_stall_total or (current_stall_total == total and abs((l.published_at-current_stall_timestamp).total_seconds()) <= 7200):
                pass
            else:
                vids_list = [item[1].video_id for item in sorted(stall, key=lambda x: x[0])]
                reordered_video_ids.extend(vids_list)
                stall = []
            current_stall_total = total
            current_stall_timestamp = l.published_at
            stall.append((int(idx), l))
        else:
            reordered_video_ids.append(vid)
    vids_list = [item[1].video_id for item in sorted(stall, key=lambda x: x[0])]
    reordered_video_ids.extend(vids_list)
    return reordered_video_ids

