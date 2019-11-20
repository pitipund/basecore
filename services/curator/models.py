# -*- coding: utf-8 -*-
import datetime
import os
import re
import urllib.request, urllib.parse, urllib.error
import hashlib
import logging
from subprocess import Popen, call
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model

try:
    from PIL import Image
except ImportError:
    import Image

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.core.files import File
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Max, Q, F
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.conf import settings
from django.utils import timezone

# from music.models import Video
from six import BytesIO, text_type

from his.penta.showtime.utils import gen_image_filename, VIDEO_TYPE_CHOICES, VideoType, AccessLevel, \
    ACCESS_LEVEL_CHOICES, UploadToDir
from his.penta.apis.utils import normalize_url

from his.penta.curator.fields import CharField3Byte, TextField3Byte

User = get_user_model()
UID_LENGTH = 255  # reference from DJANGO socialauth
MAKE_SNAPSHOT_YOUTUBE_PATH = "/home/showtime/beta_showtime/scripts/make_snapshot_from_youtube.sh"
MAKE_SNAPSHOT_STREAM_PATH = "/home/showtime/beta_showtime/scripts/make_snapshot_from_stream_url.sh"

logger = logging.getLogger(__name__)


class CuratorLanguageSupport(models.Model):
    code = models.CharField(max_length=2, unique=True, primary_key=True)
    name = models.CharField(max_length=32)
    native_name = models.CharField(max_length=64, null=True, blank=True, default=None)

    class Meta:
        app_label = 'curator'

    def get_name(self):
        if not self.native_name:
            return self.name
        return self.native_name

    def __str__(self):
        return "%s: %s" % (self.code, self.name)


class LiveChannelManager(models.Manager):
    def get_live_channels(self):
        """Return QuerySet of enabled live channels, order by sort_key"""
        return self.filter(enabled=True, redirect=False).order_by('sortkey')


class CuratorSupport(models.Model):

    objects = LiveChannelManager()

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    url = models.URLField(help_text="URL to redirect after user press icon")
    icon = models.ImageField(upload_to=settings.SUPPORT_IM_PATH, verbose_name="Icon")
    enabled = models.BooleanField(default=True)
    sortkey = models.IntegerField(default=0, help_text="Channel number")
    minversion = models.IntegerField(default=142, help_text="Minimum version of PentaTV that supports this media")
    redirect = models.BooleanField(default=False, help_text="When icon was clicked, should we redirect user to URL?")
    broadcast_by_us = models.BooleanField(default=False, help_text="This channel was broadcast by us?")
    is_digital = models.BooleanField(default=False, help_text="To indicate if this channel is digital tv channel")
    languages = models.ManyToManyField(CuratorLanguageSupport)
    is_recorded = models.BooleanField(default=False, help_text="To indicate if live recorded on our server")
    record_url = models.URLField(default="", null=True, blank=True, help_text="URL from record server")
    allow_oversea = models.BooleanField(default=True, help_text="Allow this channel to broadcast outside Thailand")

    class Meta:
        verbose_name = "Live Channel"
        app_label = 'curator'

    def __str__(self):
        return self.name

    def channel_id(self):
        return "live_%d" % self.id

    def encode(self, params):
        result = ''
        for k, v in params.items():
            result += u'&%s=%s' % (k, urllib.parse.quote(v.encode('utf8'), safe='~()*!.\''))
        return result

    def get_active_streams(self):
        return self.curatorstreamurl_set.filter(isActive=True).order_by('order_key', 'id')

    def streamUrl(self):
        streams = self.get_active_streams()
        if len(streams) >= 1:
            return streams[0]
        return None

    def pentaStreamUrl(self, request):
        stream = self.get_active_streams()
        if stream:
            host = 'stream_url'
            if text_type(stream[0]).startswith('rtmp://'):
                host = 'rtmp_url'
        else:
            return None
        params = {
            "1": text_type(stream[0]),
            "current": text_type(stream[0]),
            "title": self.name,
            "live": "1",
            "icon": request.build_absolute_uri(self.icon.url),
            "channel_id": self.channel_id()
        }
        return u'penta://%s?%s' % (host, self.encode(params))

    def get_live_item(self, request):
        item = {
            "channel_id": self.channel_id(),
            "name": self.name,
            "icon": request.build_absolute_uri(self.icon.url),
            "channel_number": self.sortkey
        }
        curatorStreamUrl = self.get_active_streams()
        streamUrl = []
        streamPrimary = []
        for i in range(len(curatorStreamUrl)):
            streamUrl.append(curatorStreamUrl[i].streamUrl)
            if curatorStreamUrl[i].isPrimary:
                streamPrimary.append(i)
        item["stream_url"] = streamUrl
        item["primary_link"] = streamPrimary
        return item

    def get_queue_items(self, request, limit=-1):
        streams = self.get_active_streams()
        if limit > 0:
            size = streams.count()
            startIdx = max(size-limit, 0)
            streams = streams[startIdx:]
        items = []
        index = 0
        for stream in streams:
            item = output = {
                "thumbnail": request.build_absolute_uri(self.icon.url),
                "video_id": str(stream) if stream else None,
                "type": "local",
                "name": self.name,
                "queue_id": "live_%d_item%d" % (self.id, index)
            }
            if stream and str(stream).startswith("rtmp"):
                item['video_id'] = 'http://127.0.0.1/rtmpplay/?url=%s' % item['video_id']

            items.append(item)
            index += 1
        return items

    def admin_icon(self):
        return '<img src="%s" height="24" border="0" />' % self.icon.url

    def real_icon(self):
        return self.icon.url

    def replace_black_color(self):
        orig_color = (0, 0, 0)
        replace_color = (25, 25, 25)
        if not self.icon:
            return
        img = Image.open(self.icon.file).convert('RGB')
        data = img.load()
        for y in range(img.size[0]):
            for x in range(img.size[1]):
                if data[y, x] == orig_color:
                    data[y, x] = replace_color
        tmp = BytesIO()
        img.save(tmp, format='PNG')
        tmp.seek(0)
        self.icon.save('%s.png' % (self.icon.name.rsplit('.', 1)[0]), File(tmp))

    def save(self, *args, **kwargs):
        if 'form' in kwargs:
            form = kwargs['form']
            del kwargs['form']
        else:
            form = None
        replace_icon = (
            self.pk is None or
            (form is not None and 'icon' in form.changed_data)
        )
        super(CuratorSupport, self).save(*args, **kwargs)
        if replace_icon:
            self.replace_black_color()

    admin_icon.allow_tags = True


class CuratorChannelQuerySet(QuerySet):

    def public_channels(self):
        return self.filter(isPrivate=False)

    def with_keyword(self, keyword):
        return self.public_channels().filter(name__icontains=keyword)

    def get_search_history_channel(self):
        penta_user = User.objects.filter(username='pentachannel-thevcgroup.com').first()
        if penta_user:
            channel_name = 'Search History'
            search_channel = self.filter(name=channel_name, user=penta_user).first()
            if not search_channel:
                search_channel = self.create(
                    name=channel_name,
                    icon="images/pentash.jpg",
                    detail=u"รวบรวมวิดีโอจากการค้นหา",
                    user=penta_user
                )
            return search_channel
        return None


class CuratorChannel(models.Model):
    upload_dir = UploadToDir(settings.ICON_PATH)

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=60)
    icon = models.ImageField(upload_to=upload_dir,
                             verbose_name="Icon", null=True, blank=True)
    icon_url = models.URLField(blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    detail = models.CharField(max_length=2000, blank=True, null=True, default="")
    isLive = models.BooleanField(default=False)
    isDefault = models.BooleanField(default=False)
    isPrivate = models.BooleanField(default=False, db_index=True)
    isOfficial = models.BooleanField(default=False)
    url_name = models.CharField(max_length=50, unique=True, blank=True,
                                null=True, default=None)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    pin_queue = models.IntegerField(blank=True, null=True)
    user_save = models.BooleanField(default=False, db_index=True)
    user_share = models.BooleanField(default=False)

    is_series_completed = models.BooleanField(default=False)
    is_create_from_auto = models.BooleanField(default=False)
    access_level = models.IntegerField(choices=ACCESS_LEVEL_CHOICES, default=AccessLevel.ANY, db_index=True)

    rank_score = models.IntegerField(default=0)  # don't want to mess up with decimal

    languages = models.ManyToManyField(CuratorLanguageSupport)

    objects = CuratorChannelQuerySet.as_manager()

    # Auto sort with regular expression
    enable_sort_pattern = models.BooleanField(default=False, help_text="enable new auto sort feature")
    auto_sort = models.BooleanField(default=False, help_text="auto sort when new video added")
    desc_sort = models.BooleanField(default=False, help_text="sort with newer first")
    episode_pattern = models.CharField(max_length=100, blank=True, default='',
                                       help_text="regex pattern of episode")
    use_date_pattern = models.BooleanField(default=False,
                                           help_text="use date pattern (disable episode pattern)")
    video_part_pattern = models.CharField(max_length=100, blank=True, default='',
                                          help_text="regex pattern of video part")

    is_checked_onair = models.BooleanField(default=False)
    is_onair = models.BooleanField(default=False)
    start_onair = models.DateTimeField(blank=True, null=True, default=None)
    live_source = models.ForeignKey(CuratorSupport, null=True, blank=True , default=None)
    schedule_monday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_monday_end = models.TimeField(blank=True, null=True, default=None)
    schedule_tuesday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_tuesday_end = models.TimeField(blank=True, null=True, default=None)
    schedule_wednesday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_wednesday_end = models.TimeField(blank=True, null=True, default=None)
    schedule_thursday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_thursday_end = models.TimeField(blank=True, null=True, default=None)
    schedule_friday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_friday_end = models.TimeField(blank=True, null=True, default=None)
    schedule_saturday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_saturday_end = models.TimeField(blank=True, null=True, default=None)
    schedule_sunday_start = models.TimeField(blank=True, null=True, default=None)
    schedule_sunday_end = models.TimeField(blank=True, null=True, default=None)

    # TODO delete this two field after use new sqool design for a while
    is_sqool = models.BooleanField(default=False)
    sqool_group = models.ForeignKey(Group, null=True, blank=True, default=None)

    class Meta:
        app_label = 'curator'
        ordering = ["-update_at"]
        permissions = (
            ('edit_all_channel', 'Edit all channels'),
        )

    def __str__(self):
        return self.name

    """    
    def is_official(self):
        if self.user.id in [29 , 2900 , 8116] and self.user_save == False and self.user_share == False:
            return 'yes'
        else:
            return 'no'
    """

    def channel_id(self):
        return "channel_%d" % self.id

    def playlist_count(self):
        return self.curatorplaylist_set.count()

    def real_icon(self):
        """Return Absolute URL to channel icon"""
        if self.user_share:
            try:
                return self.user.userprofile.real_image()
            except:
                pass
        if self.user_save:
            return os.path.join(settings.MEDIA_URL, settings.IMAGES_URL, 'saved_channel.png')
        if self.icon:
            return self.icon.url
        if self.icon_url:
            return self.icon_url
        return os.path.join(settings.MEDIA_URL, settings.THUMBNAIL_IM_PATH, 'no_content.png')

    def url(self):
        return normalize_url('channel', channel_id=self.id, channel_name=self.name)

    def api_url(self):
        return 'http://pentachannel.com/apis/channel/%s/' % self.channel_id()

    # def tags(self):
    #     return CuratorTag.objects.filter(curatorChannel=self)

    def tags_list(self):
        return list(self.tags.values('id', 'name'))

    def playlists(self):
        return self.curatorplaylist_set.all().order_by("playlist_index")

    def pin_playlist(self, playlist):
        if type(playlist) is not CuratorPlaylist:
            raise TypeError('expected CuratorPlaylist got %s' % type(playlist))
        if playlist in self.curatorplaylist_set.all():
            self.pin_queue = playlist.id
            self.save()
        else:
            raise CuratorPlaylist.DoesNotExist()

    def get_next_playlist_index(self):
        return self.curatorplaylist_set.aggregate(Max('playlist_index')).get('playlist_index__max', 1)

    def num_videos(self):
        return self.playlists().count()

    def owner(self):
        return self.user.first_name or self.user.username

    def views(self):
        try:
            count = 0
            # go straight to prevent hit database again
            user_view = self.curatorviews_set.all()
            for v in user_view:
                count += v.views
            return count
        except (CuratorViews.DoesNotExist, AttributeError):
            return 0

    def save(self, *args, **kwargs):
        if self.url_name == "":
            self.url_name = None
        if self.user.id in [29, 2900, 8116] and self.user_save == False and self.user_share == False:
            self.isOfficial = True
        super(CuratorChannel, self).save(*args, **kwargs)

    def sort_videos_by_pattern(self):
        if not self.enable_sort_pattern:
            return
        playlists = []
        # print self.episode_pattern, self.video_part_pattern
        ep_pattern = re.compile(self.episode_pattern)
        part_pattern = re.compile(self.video_part_pattern)

        ep = None
        part = None
        for playlist in self.playlists():
            name = playlist.name
            try:
                name = name.encode('utf-8')
            except UnicodeDecodeError:
                pass
            # print name
            if self.use_date_pattern:
                from .utils import get_date_from_name
                try:
                    ep = get_date_from_name(name)
                except:
                    ep = None
                # print name, ep
                if ep is None:
                    ep = playlist.link.published_at.date()
            else:
                re_ep = ep_pattern.search(name.decode('utf-8'))
                try:
                    ep = int(re_ep.group('ep'))
                except (IndexError, AttributeError):
                    ep = None
            re_part = part_pattern.search(name.decode('utf-8'))
            try:
                part = int(re_part.group('part'))
            except (IndexError, AttributeError):
                part = 1
            playlists.append([playlist, ep, part])

        if not self.episode_pattern and not self.use_date_pattern:
            # print 'sort by literature'
            playlists = sorted(playlists, reverse=self.desc_sort)
        elif not self.video_part_pattern:
            # print 'sort by episode only'
            playlists = sorted(playlists, key=lambda k: (k[1], k[0].name), reverse=self.desc_sort)
        else:
            # print 'sort by episode and part'
            def sort_key(k):
                if self.desc_sort:
                    return k[1], -k[2], k[0].name
                return k[1], k[2], k[0].name
            playlists = sorted(playlists, key=sort_key, reverse=self.desc_sort)
        with transaction.atomic():
            for i in range(0, len(playlists)):
                # print i,
                # print playlists[i]
                playlists[i][0].playlist_index = i+1
                playlists[i][0].save()


class CuratorLinkManager(models.Manager):

    def get_video_id_from_url(self, url):
        lowered_url = url.lower()
        if 'youtube.com' in lowered_url:
            try:
                parser = urlparse(url)
                return parse_qs(parser.query)['v'][0]
            except (KeyError, ValueError):
                return None
        elif 'youtu.be' in lowered_url:
            parser = urlparse(url)
            result = parser.path[1:]
            return result if result else None
        elif 'dailymotion.com' in lowered_url:
            try:
                return re.split('_|\?', url.rsplit('/', 1)[1], 1)[0]
            except IndexError:
                return url
        elif 'dai.ly' in lowered_url:
            parser = urlparse(url)
            result = parser.path[1:]
            return result if result else None
        elif 'facebook.com' in lowered_url:
            try:
                parsed_uri = urlparse(url)
                query_result = parse_qs(parsed_uri.query)
                if 'video_id' in query_result:
                    return query_result['video_id'][0]
                elif 'v' in query_result:
                    return query_result['v'][0]
                else:
                    if '/videos/' in parsed_uri.path:
                        results = parsed_uri.path.split('/')
                        results.reverse()
                        for item in results:
                            if item:
                                return item
                    return None
            except (KeyError, ValueError):
                return None
        elif 'vimeo.com' in lowered_url:
            try:
                parser = urlparse(url)
                result = parser.path.split('/')[-1]
                return result if result else None
            except Exception as e:
                logger.exception("Error parsing vimeo url")
        return url

    def get_video_type_from_url(self, url):
        parsed_uri = urlparse(url.lower())
        if not parsed_uri.scheme:
            parsed_uri = urlparse('http://'+url)
        domain = parsed_uri.netloc
        scheme = parsed_uri.scheme
        path = parsed_uri.path
        if domain or scheme or path:
            if domain.endswith(('youtube.com', 'youtu.be',)):
                return VideoType.YOUTUBE
            elif domain.endswith(('dailymotion.com', 'dai.ly',)):
                return VideoType.DAILYMOTION
            elif domain.endswith('facebook.com'):
                return VideoType.FACEBOOK
            elif domain.endswith('vimeo.com'):
                return VideoType.VIMEO
            elif scheme == 'rtmp':
                return VideoType.RTMP
            elif scheme == 'rtsp':
                return VideoType.RTSP
            elif path.endswith('.m3u8'):
                return VideoType.M3U8
            elif path.endswith('.mp4'):
                return VideoType.STREAM_URL
        return None

    def get_video_description_from_url(self, url):
        desc = ''
        if url:
            video_id = self.get_video_id_from_url(url)
            if video_id:
                video_type = self.get_video_type_from_url(url)
                if video_type == VideoType.YOUTUBE:
                    from .utils import utils_curator_get25_youtube
                    result = utils_curator_get25_youtube(video_id, False)
                    if result[0] and len(result[1]) > 0:
                        desc = result[1][0].get('payload', '')
                elif video_type == VideoType.DAILYMOTION:
                    from .utils import utils_curator_getInfo_dailymotion
                    result = utils_curator_getInfo_dailymotion(url)
                    if result[0] and type(result[1]) == dict:
                        desc = result[1].get('payload', '')
                elif video_type == VideoType.FACEBOOK:
                    from .utils import utils_curator_getInfo_facebook
                    result = utils_curator_getInfo_facebook(video_id)
                    if result[0] and type(result[1]) == dict:
                        desc = result[1].get('payload', '')
                        if desc is None:
                            desc = ''
        return desc

    def _create_link(self, url, name, info):
        from .utils import get_local_datetime

        return CuratorLink.objects.create(
            name=name, url=url, duration_s=info["duration"], video_type=info["v_type"], video_id=info["v_id"],
            provider_id=info.get('p_id', None), provider_name=info.get('p_name', None), thumbnail_url=info.get('thumbnail', ''),
            payload=info.get("payload", ''), published_at=get_local_datetime(info.get('publish', None)))

    def _create_link_live_url(self, url, name, v_type):
        return CuratorLink.objects.create(name=name, url=url, duration_s=1, video_type=v_type, video_id=url,
                                          thumbnail=os.path.join('images', 'live_link.png'))

    def _create_youtube(self, url):  # playlist=None: update curatorlink, else: create curatorlink
        video_id = self.get_video_id_from_url(url)
        from .utils import utils_curator_get25_youtube
        success, result = utils_curator_get25_youtube(video_id, False)
        if success:
            if not result:
                raise LookupError("Invalid url %s" % url)
            return self._create_link(url, result[0]["title"], result[0])
        return None

    def _create_dailymotion(self, url):
        from .utils import utils_curator_getInfo_dailymotion
        success, result = utils_curator_getInfo_dailymotion(url)
        if success:
            return self._create_link(result["url"] or url, result["title"], result)
        return None

    def _create_facebook(self, url):
        from .utils import utils_curator_getInfo_facebook
        video_id = self.get_video_id_from_url(url)
        success, result = utils_curator_getInfo_facebook(video_id)
        # print success, result
        if success:
            return self._create_link(url, result["title"], result)
        return None

    def _create_vimeo(self, url):
        from .utils import utils_curator_getInfo_vimeo
        success, result = utils_curator_getInfo_vimeo(url)
        if success:
            return self._create_link(url, result["title"], result)
        return None

    def _create_stream(self, url, name, video_id, thumbnail_url, duration, payload=None):
        info = {'title': name,
                'duration': duration,
                'v_type': 'S',
                'v_id': video_id,
                'thumbnail': thumbnail_url,
                'payload': payload}
        return self._create_link(url, name, info)

    def _create_video(self, url, name=""):
        lowered_url = url.lower()
        if 'youtube.com' in lowered_url or 'youtu.be' in lowered_url:
            link = self._create_youtube(url)
        elif 'dailymotion.com' in lowered_url:
            link = self._create_dailymotion(url)
        elif 'facebook.com' in lowered_url:
            link = self._create_facebook(url)
        elif 'vimeo.com' in lowered_url:
            link = self._create_vimeo(url)
        elif ('googleusercontent.com' in lowered_url or 'blogspot.com' in lowered_url) and '=m' in lowered_url:
            link = self._create_link_live_url(url, "Stream Url", VideoType.STREAM_URL)
        elif 'rtmp://' in lowered_url:
            link = self._create_link_live_url(url, name or "live", VideoType.RTMP)
        elif '.m3u8' in lowered_url:
            link = self._create_link_live_url(url, name or "live", VideoType.M3U8)
        elif '.mp4' in lowered_url:
            link = self._create_link_live_url(url, "Stream Url", VideoType.STREAM_URL)
        elif 'rtsp://' in lowered_url:
            link = self._create_link_live_url(url, name or "live", VideoType.RTSP)
        else:
            raise ValueError("Type not supported")
        return link

    def get_video_link(self, url, stream_info=None):
        """
        Get link from database if exist, else create new link.
        May raise LookupError if url is invalid
        and raise ValueError if video is not supported type
        :param url: url of target video
        :return: CuratorLink of given url
        """
        key = self.get_video_id_from_url(url)
        if not key:
            raise LookupError("Invalid url")
        if stream_info is not None:
            links = self.filter(video_id=stream_info.get('video_id', url)).order_by('id')
        else:
            links = self.filter(video_id=key).order_by('id')
        if not links:
            links = (self.exclude(video_type__in=[VideoType.YOUTUBE, VideoType.DAILYMOTION,
                                                  VideoType.VIMEO, VideoType.FACEBOOK])
                     .filter(url__contains=key).order_by('id'))
        if links:
            link = links.first()
        else:
            if stream_info:
                try:
                    link = self._create_stream(url, stream_info['name'],
                                               stream_info['video_id'],
                                               stream_info['thumbnail_url'],
                                               stream_info['duration'],
                                               stream_info.get('payload', None))
                except IndexError:
                    raise IndexError('stream_info must contain name, video_id, thumbnail_url, duration, '
                                     'and (optional) payload')
            else:
                link = self._create_video(url)
        if not link:
            raise LookupError("Owner not allow or invalid URL")
        return link


class CuratorLink(models.Model):
    upload_dir = UploadToDir(settings.THUMBNAIL_PATH)
    objects = CuratorLinkManager()

    id = models.AutoField(primary_key=True)
    name = CharField3Byte(max_length=200)
    url = models.URLField()
    duration_s = models.IntegerField()
    video_type = models.CharField(max_length=1, choices=VIDEO_TYPE_CHOICES, db_index=True)
    video_id = models.CharField(max_length=500, blank=True, null=True, db_index=True)
    provider_id = models.CharField(max_length=500, blank=True, null=True)
    provider_name = models.CharField(max_length=500, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=upload_dir,
                                  verbose_name="thumbnail", blank=True, null=True)
    thumbnail_url = models.CharField(max_length=300, blank=True)
    snapshot_url = models.CharField(max_length=200, blank=True, null=True)
    link_index = models.IntegerField(default=1)
    isAvailable = models.BooleanField(default=True)
    payload = TextField3Byte(blank=True, null=True)
    # last_playlist_create_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        app_label = 'curator'

    def duration(self):
        duration = ""
        if self.duration_s:
            m, s = divmod(self.duration_s, 60)
            h, m = divmod(m, 60)
            if h:
                duration = "%d:%02d:%02d" % (h, m, s)
            else:
                duration = "%d:%02d" % (m, s)
        return duration

    def create_snapshot(self):
        md5 = hashlib.md5(self.url.encode('utf-8'))
        folder_id = md5.hexdigest()
        if self.video_type == VideoType.YOUTUBE or self.video_type == VideoType.DAILYMOTION or self.video_type == 'V':
            ret = call([MAKE_SNAPSHOT_YOUTUBE_PATH, self.url, folder_id])
            self.snapshot_url = folder_id
        elif self.video_type == 'M':
            '''skip M3U8'''
            ret = 0
            pass
        else:
            ret = call([MAKE_SNAPSHOT_STREAM_PATH, self.video_id, folder_id])
            self.snapshot_url = folder_id
        return ret == 0

    def save(self, *args, **kwargs):
        if not self.pk:
            md5 = hashlib.md5(self.url.encode('utf-8'))
            folder_id = md5.hexdigest()
            if getattr(settings, 'VIDEO_SNAPSHOT_ENABLED'):
                if self.video_type == VideoType.YOUTUBE or self.video_type == VideoType.DAILYMOTION \
                        or self.video_type == 'V':
                    Popen([MAKE_SNAPSHOT_YOUTUBE_PATH, self.url, folder_id])
                    self.snapshot_url = folder_id
                elif self.video_type == 'M':
                    '''skip M3U8'''
                    pass
                else:
                    Popen([MAKE_SNAPSHOT_STREAM_PATH, self.video_id, folder_id])
                    self.snapshot_url = folder_id

        super(CuratorLink, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def real_thumbnail(self):
        if self.thumbnail_url:
            return self.thumbnail_url
        if self.thumbnail:
            return self.thumbnail.url
        return settings.MEDIA_URL + "images/live_link.png"

    def real_snapshot(self):
        if self.snapshot_url:
            return settings.MEDIA_URL + "snapshot/" + self.snapshot_url + "/01.jpg"
        else:
            return self.real_thumbnail()

    def create_new_playlist(self, channel, name="", detail=None,
                            isDefault=False, playlist_index=None,
                            user_like=None, tags=None, from_rules_auto=False,
                            play_start_at=None, play_end_at=None):
        """
        raise CuratorChannel.DoesNotExist if given channel_id but not found
        raise TypeError if doesn't get CuratorChannel or int for channel
        """
        user_like = user_like or []
        tags = tags or []
        if type(channel) is int:
            channel = CuratorChannel.objects.get(pk=channel)
        elif type(channel) is not CuratorChannel:
            raise TypeError('expected CuratorChannel or int but got %s' % type(channel))

        if self.name == '' and detail:
            # got link with 'no name' (StreamURL), we use detail as link name
            self.name = detail
            self.save()
        if not name:
            name = self.name
        keys = CuratorLinkKey.objects.filter(channel=channel)
        for key in keys:
            name = name.lower().replace(key.name.lower(), '').strip()
        if not playlist_index:
            playlist_index = channel.get_next_playlist_index()
        playlist = CuratorPlaylist.objects.create(channel=channel, name=name, detail=detail, isDefault=isDefault,
                                                  playlist_index=playlist_index, link=self, from_rules_auto=from_rules_auto,
                                                  play_start_at=play_start_at , play_end_at=play_end_at)
        tags = tags if type(tags) is list else [tags]
        tags_model = CuratorTag.objects.filter(id__in=tags)
        for t in tags_model:
            t.curatorPlaylist.add(playlist)
        for u in user_like:
            playlist.user_like.add(u)

        return playlist


class CuratorPlaylistQuerySet(QuerySet):

    """Common methods to get playlist in room/feed"""
    def with_tag(self, tag):
        """
        Get playlists corresponding to selected tag and collect relevant data for further processing
        """
        if not isinstance(tag, CuratorTag):
            tag = CuratorTag.objects.get(id=tag)

        return self.filter(Q(tags=tag) |
                           Q(channel__in=tag.curatorChannel.all())
                           ).order_by('-create_at')

    def with_keyword(self, keyword):
        return self.filter(Q(name__icontains=keyword) |
                           Q(channel__name__icontains=keyword))

    def getPlaylistDescription(self, user, playlist):
        detail = playlist.detail or ""
        try:
            channel = playlist.channel
            channel.image = channel.real_icon()
            owner = playlist.channel.user
            owner.showname = owner.first_name + " " + owner.last_name

            try:
                user_image = owner.userprofile.real_image()
            except Exception:
                user_image = settings.MEDIA_URL + 'uploaded/profile/no_user.png'

            description = {"playlist_id": playlist.id, "own": owner == user, "usershowname": owner.showname,
                           "userimage": user_image,
                           "channelname": channel.name, "channelimage": channel.image, "channelid": channel.id,
                           "detail": detail, "playlist_index": playlist.playlist_index, "create_at": playlist.create_at,
                           "liked": True if not user.is_anonymous() and
                                            playlist.user_like.filter(id=user.id) else False,
                           "like_count": playlist.user_like.all().count()}
        except AttributeError:
            description = {"usershowname": "Unknown", "userimage": "",
                           "channelname": "Unknown", "channelimage": "",
                           "detail": detail, "playlist_index": None,
                           "liked": False, "like_count": 0}

        return description

    def group_by_link(self, user=None, saved_links=[]):
        """This method group playlist with same CuratorLink together

        Return list of playlist to be displayed in roomView/searchView
        [ {'count': 1,
           'description': [{'channelid': 6449L,
                   'channelimage': '/media/uploaded/icon/222.jpg',
                   'channelname': u'\u0e40\u0e25\u0e37\u0e2d\u0e14\u0e21\u0e31\u0e07\u0e01\u0e23 (\u0e2a\u0e34\u0e07\u0e2b\u0e4c) [\u0e08\u0e1a]',
                   'create_at': datetime.datetime(2015, 5, 6, 13, 58, 16, tzinfo=<UTC>),
                   'detail': '',
                   'like_count': 0,
                   'liked': False,
                   'own': False,
                   'playlist_id': 91899L,
                   'playlist_index': 38L,
                   'userimage': '/media/uploaded/profile/13629748171362975070l.jpg',
                   'usershowname': u'runranrun -'}],
          'duration': 12.466666666666667,
          'image': u'http://img.youtube.com/vi/F__SUs72514/0.jpg',
          'name': u'\u0e40\u0e25\u0e37\u0e2d\u0e14\u0e21\u0e31\u0e07\u0e01\u0e23 - \u0e2a\u0e34\u0e07\u0e2b\u0e4c LueadMungKorn-Singh Ep.8 \u0e15\u0e2d\u0e19\u0e17\u0e35\u0e48 7/9 | 05-05-58 | TV3 Official',
          'playlist_id': 91899L,
          'saved': False,
          'thumbnail': None,
          'upload_description': u'\u0e19\u0e33\u0e41\u0e2a\u0e14\u0e07\u0e42\u0e14\u0e22:  \u0e15\u0e34\u0e4a\u0e01 \u0e40\u0e08\u0e29\u0e0e\u0e32\u0e20\u0e23\u0e13\u0e4c , \u0e21\u0e34\u0e27 \u0e19\u0e34\u0e29\u0e10\u0e32 , \u0e2d\u0e39\u0e4b \u0e18\u0e19\u0e32\u0e01\u0e23 , \u0e2b\u0e0d\u0e34\u0e07 \u0e23\u0e10\u0e32 , \u0e19\u0e07 \u0e17\u0e19\u0e07\u0e28\u0e31\u0e01\u0e14\u0e34\u0e4c , \u0e42\u0e2d \u0e2d\u0e19\u0e38\u0e0a\u0e34\u0e15 , \u0e42\u0e22 \u0e17\u0e31\u0e28\u0e19\u0e4c\u0e27\u0e23\u0e23\u0e13 \u0e41\u0e25\u0e30\u0e19\u0e31\u0e01\u0e41\u0e2a\u0e14\u0e07\u0e21\u0e32\u0e01\u0e1d\u0e35\u0e21\u0e37\u0e2d\u0e04\u0e31\u0e1a\u0e04\u0e31\u0e48\u0e07\n\u0e1a\u0e17\u0e25\u0e30\u0e04\u0e23\u0e42\u0e14\u0e22: \u0e25\u0e34\u0e0b\n\u0e2d\u0e33\u0e19\u0e27\u0e22\u0e01\u0e32\u0e23\u0e1c\u0e25\u0e34\u0e15\u0e42\u0e14\u0e22: \u0e1a\u0e23\u0e34\u0e29\u0e31\u0e17 \u0e41\u0e2d\u0e04 \u0e2d\u0e32\u0e23\u0e4c\u0e15 \u0e40\u0e08\u0e40\u0e19\u0e40\u0e23\u0e0a\u0e31\u0e48\u0e19 \u0e08\u0e33\u0e01\u0e31\u0e14 \n\u0e01\u0e33\u0e01\u0e31\u0e1a\u0e01\u0e32\u0e23\u0e41\u0e2a\u0e14\u0e07\u0e42\u0e14\u0e22: \u0e1a\u0e31\u0e13\u0e11\u0e34\u0e15 \u0e17\u0e2d\u0e07\u0e14\u0e35\n\u0e2d\u0e2d\u0e01\u0e2d\u0e32\u0e01\u0e32\u0e28\u0e17\u0e38\u0e01\u0e27\u0e31\u0e19\u0e08\u0e31\u0e19\u0e17\u0e23\u0e4c\u2013\u0e2d\u0e31\u0e07\u0e04\u0e32\u0e23 \u0e40\u0e27\u0e25\u0e32 20:15\u201322:45 \u0e19.\n\nSUBSCRIBE: http://www.youtube.com/tv3official\n\u0e40\u0e1e\u0e25\u0e07\u0e1b\u0e23\u0e30\u0e01\u0e2d\u0e1a\u0e25\u0e30\u0e04\u0e23 : https://www.youtube.com/watch?v=Y00RIZvxS2I\n\u0e14\u0e39\u0e22\u0e49\u0e2d\u0e19\u0e2b\u0e25\u0e31\u0e07\u0e44\u0e14\u0e49\u0e17\u0e35\u0e48 : https://www.youtube.com/playlist?list=PL0VVVtBqsourzRMrgFFepEWHQnLx3_WEf',
          'url': u'https://www.youtube.com/watch?v=F__SUs72514&index=7&list=PL0VVVtBqsourzRMrgFFepEWHQnLx3_WEf',
          'video_id': u'F__SUs72514',
          'video_type': u'Y'}
        ]"""
        user = user if user else AnonymousUser()
        ret_dict = []
        ret_set = {}
        qs = self.prefetch_related('user_like', 'channel__user__userprofile')\
                 .select_related('channel', 'link')
        for playlist in qs:
            link = playlist.link
            if link.id not in ret_set:
                ret_set[link.id] = {'url': link.url,
                                    'image': link.thumbnail_url, 'thumbnail': link.snapshot_url,
                                    'name': link.name, 'count': 0,
                                    'video_id': link.video_id, 'playlist_id': playlist.id,
                                    'video_type': link.video_type, 'duration': link.duration_s / 60.0,
                                    'description': [], 'upload_description': link.payload,
                                    'saved': link in saved_links}
                ret_dict.append(ret_set[link.id])

            detail = self.getPlaylistDescription(user, playlist)
            if detail['channelname'] != "Unknown":
                ret_set[link.id]['description'].append(detail)
            ret_set[link.id]['count'] += 1
        return ret_dict


class CuratorPlaylist(models.Model):
    objects = CuratorPlaylistQuerySet.as_manager()

    id = models.AutoField(primary_key=True)
    name = CharField3Byte(max_length=200)
    link = models.ForeignKey(CuratorLink, related_name="playlists")
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now_add=True)
    detail = CharField3Byte(max_length=2000, blank=True, null=True)
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True)
    isDefault = models.BooleanField(default=False)
    playlist_index = models.IntegerField(default=1)
    user_like = models.ManyToManyField(settings.AUTH_USER_MODEL)
    play_start_at = models.IntegerField(null=True, blank=True)
    play_end_at = models.IntegerField(null=True, blank=True)
    from_rules_auto = models.BooleanField(default=False)
    sub_access_level = models.IntegerField(choices=ACCESS_LEVEL_CHOICES, default=AccessLevel.ANY, db_index=True)
    # music_extension = models.ForeignKey(Video, null=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return self.name

    def url(self):
        if self.channel:
            return normalize_url('playlist', channel_id=self.channel_id, channel_name=self.channel.name,
                                 playlist_id=self.id, playlist_name=self.name)

    def get_link(self):
        return self.link.name

    def views(self):
        try:
            count = 0
            # go straight to prevent hit database again
            user_views = self.curatorviews_set.all()
            for v in user_views:
                count += v.views
            return count
        except (CuratorViews.DoesNotExist, AttributeError):
            return 0

    def is_watched(self):
        return self.curatoruserwatched_set.exists()

    def pin(self):
        self.channel.pin_playlist(self)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.channel:
                last_in_playlist = CuratorPlaylist.objects.filter(channel=self.channel).aggregate(Max('playlist_index'))
                if last_in_playlist.get('playlist_index__max') is None:
                    self.playlist_index = 1
                else:
                    self.playlist_index = last_in_playlist.get('playlist_index__max') + 1

                # [PENG] place here instead
                self.channel.update_at = timezone.now()
                self.channel.save()

        super(CuratorPlaylist, self).save(*args, **kwargs)

        # [PENG] decide to not update 'update_at' field in channel from any save in playlist, just only new clip founded case
        #if self.channel:
        #    self.channel.update_at = timezone.now()
        #    self.channel.save()

        # comment out because unuse
        # if self.link:
        #     self.link.last_playlist_create_at = self.create_at
        #     self.link.save()

    get_link.admin_order_field = 'name'


# extend of playlist, only a few playlists have this one
class CuratorPlaylistExtra(models.Model):

    playlist = models.OneToOneField(CuratorPlaylist, primary_key=True, related_name='extra')
    open_for_question = models.BooleanField(default=False)


class ViewsManager(models.Manager):
    def _create_views(self, o_type, obj):
        view = None
        if o_type == "channel":
            view = self.model(curatorChannel=obj, views=1)
        elif o_type == "playlist":
            view = self.model(curatorPlaylist=obj, views=1)
        if view:
            view.save(using=self._db)

    @transaction.atomic
    def create_views(self, o_type, obj):
        if o_type == "channel":
            try:
                view, is_create = CuratorViews.objects.get_or_create(curatorChannel=obj)
            except CuratorViews.MultipleObjectsReturned:
                views = CuratorViews.objects.filter(curatorChannel=obj)
                view = views.first()
                for v in views[1:]:
                    view.views += v.views
                    v.delete()
            view.views += 1
            view.save()
        elif o_type == "playlist":
            try:
                view, is_create = CuratorViews.objects.get_or_create(curatorPlaylist=obj)
            except CuratorViews.MultipleObjectsReturned:
                views = CuratorViews.objects.filter(curatorPlaylist=obj)
                view = views.first()
                for v in views[1:]:
                    view.views += v.views
                    v.delete()
            view.views += 1
            view.save()


class CuratorViews(models.Model):

    objects = ViewsManager()

    id = models.AutoField(primary_key=True)
    curatorChannel = models.ForeignKey(CuratorChannel, blank=True, null=True)
    curatorPlaylist = models.ForeignKey(CuratorPlaylist, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)

    def __str__(self):
        return "%s - %s : - %s" % (self.curatorChannel, self.curatorPlaylist, self.views)


class CuratorTagQuerySet(QuerySet):
    def clean_unused_tags(self):
        (self.filter(curatorChannel=None, curatorPlaylist=None)
             .exclude(id__in=[settings.TAG_POPULAR_ID, settings.TAG_NEW_CHANNEL_ID,
                              settings.TAG_LIVE_CHANNEL_ID])).delete()


class CuratorTag(models.Model):
    ORDER_BY_RATING = 'R'
    ORDER_BY_UPDATE = 'U'
    ORDER_BY_NEWEST = 'N'
    ORDER_BY_RANDOM = 'D'
    ORDER_BY_VIEW = 'V'
    ORDER_BY_ROCKLOG = 'L'
    ORDER_CHOICES = (
        (ORDER_BY_RATING, 'number of follow on website + follow on penta last 7 days'),
        (ORDER_BY_UPDATE, 'last update first'),
        (ORDER_BY_NEWEST, 'newest first'),
        (ORDER_BY_RANDOM, 'random'),
        (ORDER_BY_VIEW, 'number of views on website last 7 days'),
        (ORDER_BY_ROCKLOG, 'number of views on penta last 30 days'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    name_en = models.CharField(max_length=50, default='n/a')
    curatorChannel = models.ManyToManyField(CuratorChannel, related_name='tags')
    curatorPlaylist = models.ManyToManyField(CuratorPlaylist, related_name='tags')
    show_in_listpage = models.BooleanField(default=False)
    show_in_listpage_index = models.IntegerField(blank=True, default=0)
    channel_show = models.ManyToManyField(CuratorChannel, related_name='channel_show',
                                          help_text='Channel show on list')
    order_preference = models.CharField(max_length=1, default=ORDER_BY_RATING, choices=ORDER_CHOICES)

    objects = CuratorTagQuerySet.as_manager()

    parent = models.ForeignKey("self", blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.name, self.curatorChannel.all() or self.curatorPlaylist.all())

    def get_curatorChannel(self):
        return self.curatorChannel.all()

    def get_curatorPlaylist(self):
        return self.curatorPlaylist.all()

    def get_channel_show(self):
        return self.channel_show.all()

    def url(self):
        return normalize_url('tag', tag_id=self.id, tag_name=self.name)

    class Meta:
        app_label = 'curator'


class CuratorLike(models.Model):
    id = models.AutoField(primary_key=True)
    curatorPlaylist = models.ForeignKey(CuratorPlaylist, blank=True, null=True)
    likes = models.IntegerField()
    dislikes = models.IntegerField()

    class Meta:
        app_label = 'curator'


class CuratorComment(models.Model):
    id = models.AutoField(primary_key=True)
    curatorPlaylist = models.ForeignKey(CuratorPlaylist, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    message = models.CharField(max_length=500)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'curator'


class UserDetail(models.Model):
    """Penta's specific detail of the user model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='userdetail')
    receive_mail = models.BooleanField(default=True)
    last_send_update_mail = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'curator'

    def is_facebook_user(self):
        if self.user.userprofile is None:
            return False
        return self.user.userprofile.facebook_id is not None

    def get_full_name(self):
        full_name = '%s %s' % (self.user.first_name, self.user.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.user.first_name

    def get_share_channel(self):
        try:  # share channel already exists
            share_channel = CuratorChannel.objects.get(user_share=True, user=self.user)
        except CuratorChannel.DoesNotExist:  # create default share channel
            share_channel = CuratorChannel.objects.create(name=self.get_full_name(),
                                                          icon=None,
                                                          user_share=True,
                                                          user=self.user)
        return share_channel

    def get_saved_channel(self):
        try:  # share channel already exists
            save_channel = CuratorChannel.objects.get(user_save=True, user=self.user)
        except CuratorChannel.DoesNotExist:  # create default save channel
            save_channel = CuratorChannel.objects.create(name="Saved Video",
                                                         icon=None,
                                                         user_save=True,
                                                         isPrivate=True,
                                                         user=self.user)
        return save_channel


# class User(AbstractBaseUser, PermissionsMixin):
#     username = models.CharField(_('username'), max_length=50, unique=True,
#                                 help_text=_('Required. 50 characters or fewer. Letters, numbers and '
#                                             '@/./+/-/_ characters'),
#                                 validators=[
#                                     validators.RegexValidator(re.compile('^[\w.@+-]+$'), _('Enter a valid username.'),
#                                                               'invalid')])
#     USERNAME_FIELD = 'username'


class UserProfile(models.Model):
    """User profile from facebook"""
    upload_dir = UploadToDir(settings.PROFILE_PATH)

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='userprofile')
    url_name = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to=upload_dir,
                              blank=True, null=True, verbose_name="Profile image")
    image_url = models.URLField(blank=True, null=True)
    isDisplay_email = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=UID_LENGTH, null=False, blank=True, default='')
    facebook_access_token = models.TextField(null=False, blank=True, default='')
    facebook_expires = models.IntegerField(null=True, default=0)
    last_visit_follow_page = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return 'UserProfile: ' + self.user.username

    def user_url(self):
        # if self.url_name:
        #     return self.url_name
        # else:
        #     return self.user.id
        return self.user.id

    def real_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return os.path.join(settings.MEDIA_URL, settings.PROFILE_PATH, 'no_user.png')

    def save(self, *args, **kwargs):
        if self.image_url:
            if "?" not in self.image_url:
                if self.image_url.startswith("http://"):
                    self.image_url = self.image_url[5:]
                elif self.image_url.startswith("https://"):
                    self.image_url = self.image_url[6:]
                if "?width=240&height=240" not in self.image_url:
                    self.image_url = self.image_url + "?width=240&height=240"
        super(UserProfile, self).save(*args, **kwargs)


class UserFollow(models.Model):
    id = models.AutoField(primary_key=True)
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='Follower')
    following = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='Following')

    class Meta:
        app_label = 'curator'

    def get_following(self):
        return self.following.all()


class CuratorStreamUrl(models.Model):
    id = models.AutoField(primary_key=True)
    support = models.ForeignKey(CuratorSupport, null=True)
    streamUrl = models.CharField(max_length=1000, blank=True, null=True)
    referrerUrl = models.CharField(max_length=1000, blank=True, null=True)
    isActive = models.BooleanField(default=False)
    order_key = models.IntegerField(default=1)
    isPrimary = models.BooleanField(default=False)
    volume = models.IntegerField(default=0)
    note = models.CharField(default='', max_length=200, blank=True)
    is_toggle_all = models.BooleanField(default=False,
                                        help_text='Is last configured by utils.toggle_all()')

    class Meta:
        app_label = 'curator'
        ordering = ['-isActive', 'order_key', 'id']

    def __str__(self):
        return self.streamUrl

    def save(self, *args, **kwargs):
        self.is_toggle_all = False
        return super(CuratorStreamUrl, self).save(*args, **kwargs)


class CuratorLinkKey(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    channel = models.ForeignKey(CuratorChannel)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return self.name


class CuratorStat(models.Model):
    id = models.AutoField(primary_key=True)
    curatorStreamUrl = models.ForeignKey(CuratorStreamUrl, null=True, db_column='curatorStreamUrl_id',
                                         blank=True)  # Field name made lowercase.
    asr_short = models.FloatField(default=0)
    acd_short = models.IntegerField(default=0)
    total_short = models.IntegerField(default=0)
    success_short = models.IntegerField(default=0)
    duration_short = models.IntegerField(default=0)
    asr_long = models.FloatField(default=0)
    acd_long = models.IntegerField(default=0)
    total_long = models.IntegerField(default=0)
    success_long = models.IntegerField(default=0)
    duration_long = models.IntegerField(default=0)

    class Meta:
        app_label = 'curator'
        db_table = u'curator_curatorstat'


class PentaSubscript(models.Model):
    id = models.AutoField(primary_key=True)
    penta = models.CharField(max_length=100, db_index=True)
    update_at = models.DateTimeField(auto_now=True)
    curatorChannel = models.ForeignKey(CuratorChannel, blank=True, null=True)
    curatorSupport = models.ForeignKey(CuratorSupport, blank=True, null=True)

    class Meta:
        app_label = 'curator'


class UserHaveChannel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="following")
    curatorChannel = models.ForeignKey(CuratorChannel, blank=True, null=True, related_name="followers")
    liveChannel = models.ForeignKey(CuratorStreamUrl, blank=True, null=True)
    pin_queue = models.IntegerField(blank=True, null=True)
    subscribed = models.BooleanField(default=True)
    follow_at = models.DateTimeField(auto_now_add=True)

    unwatch_count = models.IntegerField(default=0)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return "%s" % self.id


# Poll every 5 minute
class LiveChannelLogManager(models.Manager):
    def create_live_channel_log(self, user, support, streamUrl, status):
        current_time = timezone.now()
        logs = LiveChannelLog.objects.filter(support=support, streamUrl=streamUrl,
                                             create_at__range=[current_time - datetime.timedelta(hours=1),
                                                               current_time])
        if logs:
            log = logs.last()
            log.user = user

            # if latest log is bad/ack and status was changed, perform update instead of create
            if not (log.status == 'A' and status == 'B') and log.status != status:
                log.status = status
                log.create_at = timezone.now()
            log.save()
            return log
        else:
            log = self.model(user=user, support=support, streamUrl=streamUrl, status=status)
            log.save(using=self._db)
            return log

    def create_curator_live_log(self, user, curator_playlist, status):
        current_time = timezone.now()
        logs = LiveChannelLog.objects.filter(curator_playlist=curator_playlist,
                                             create_at__range=[current_time - datetime.timedelta(hours=1),
                                                               current_time])
        if logs:
            log = logs.last()
            log.user = user

            # if latest log is bad/ack and status was changed, perform update instead of create
            if not (log.status == 'A' and status == 'B') and log.status != status:
                log.status = status
                log.create_at = timezone.now()
            log.save()
            return log
        else:
            log = self.model(user=user, curator_playlist=curator_playlist, status=status)
            log.save(using=self._db)
            return log


class LiveChannelLog(models.Model):

    objects = LiveChannelLogManager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    curator_playlist = models.ForeignKey(CuratorPlaylist, blank=True, null=True)
    support = models.ForeignKey(CuratorSupport, blank=True, null=True)
    streamUrl = models.ForeignKey(CuratorStreamUrl, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    STATUS_CHOICE = (
        ('G', 'Good'),
        ('A', 'Acknowledge'),
        ('R', 'Restart'),
        ('L', 'Low Buffer'),
        ('S', 'Skip'),
        ('B', 'Bad')
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICE)

    class Meta:
        app_label = 'curator'
        get_latest_by = 'create_at'

    def get_full_status(self):
        for k, v in LiveChannelLog.STATUS_CHOICE:
            if self.status == k:
                return v
        return ""


class LogManager(models.Manager):
    def _create_log(self, detail, category, ref_id, action, user):
        current_time = timezone.now()
        previouslog = CuratorLog.objects.filter(user=user, ref_id=ref_id,
                                                create_at__range=[current_time - datetime.timedelta(minutes=30),
                                                                  current_time], action=action, category=category)
        if previouslog:
            previouslog[0].detail = detail
            previouslog[0].save()
        else:
            log = self.model(detail=detail, category=category, ref_id=ref_id, action=action, user=user)
            log.save(using=self._db)

    def create_apis_log(self, obj, user, action):
        self._create_log(obj.name[:500], "A", obj.id, action, user)

    def create_action_log(self, obj, user, action):
        if obj.__class__.__name__ == 'CuratorChannel':
            category = "H"
            detail = "%s %s" % (obj.name, obj.detail)
        elif obj.__class__.__name__ == 'CuratorPlaylist':
            category = "P"
            detail = "%s %s" % (obj.name, obj.detail)
        elif obj.__class__.__name__ == 'CuratorLink':
            category = "L"
            detail = "%s - channel: %s - playlist: %s" % (
                obj.name, obj.playlists.values('channel__name')[0]['channel__name'],
                obj.playlists.values()[0]['name'])
        elif obj.__class__.__name__ == 'User':
            category = "U"
            detail = "%s - %s %s" % (obj.username, obj.first_name, obj.last_name)
        elif obj.__class__.__name__ == 'CuratorStreamUrl':
            category = "S"
            detail = obj.support.name
        self._create_log(detail[:500], category, obj.id, action, user)

    def create_follow_log(self, obj, user, action):
        if obj.__class__.__name__ == 'CuratorChannel':
            category = 'H'
        elif obj.__class__.__name__ == 'CuratorStreamUrl':
            category = 'S'

        if action == "F":
            isLog = CuratorLog.objects.filter(user=user, ref_id=obj.id, action="N", category=category)
        elif action == "N":
            isLog = CuratorLog.objects.filter(user=user, ref_id=obj.id, action="F", category=category)
        if isLog:
            isLog[0].action = action
            isLog[0].save()
        else:
            if obj.__class__.__name__ == 'CuratorChannel':
                detail = "%s %s" % (obj.name, obj.detail)
            elif obj.__class__.__name__ == 'CuratorStreamUrl':
                detail = obj.support.name
            self._create_log(detail[:500], category, obj.id, action, user)


class CuratorLog(models.Model):

    objects = LogManager()

    id = models.AutoField(primary_key=True)
    detail = models.CharField(max_length=500, blank=True, null=True)
    CATEGORY_CHOICE = (
        ('H', 'Curator Channel'),
        ('P', 'Curator Playlist'),
        ('L', 'Curator Link'),
        ('U', 'User'),
        ('A', 'API'),
        ('S', 'Live Channel')
    )
    category = models.CharField(max_length=1, choices=CATEGORY_CHOICE, db_index=True)
    ref_id = models.IntegerField(blank=True, null=True)
    ACTION_CHOICES = (
        ('C', 'Create'),
        ('E', 'Edit'),
        ('D', 'Delete'),
        ('W', 'Watch'),
        ('L', 'Like'),
        ('I', 'Dislike'),
        ('M', 'Comment'),
        ('F', 'Follow'),
        ('N', 'Unfollow'),
        ('T', 'Access tag'),
        ('H', 'Access channel')
    )
    action = models.CharField(max_length=1, choices=ACTION_CHOICES, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return "%s - %s - %s" % (self.category, self.action, self.user)


class RockLog(models.Model):
    """ possible event
        CLICK_CONTINUE_NO*      select no on lobby screen to no play latest video
        CLICK_CONTINUE_YES*     select yes on lobby screen to continue play latest video
        CLICK_FOLLOW            user click follow in penta channel
        CLICK_FOLLOW_AND_PLAY   user click play channel in penta channel
        CLICK_UNFOLLOW          user unfollow channel in penta channel
        CLICK_LIVE_GRID         user select live channel in live tab
        CLICK_LIVE_PIN*         user select live that pin on sidebar
        CLICK_PPG               user select live channel from ppg tab
        PLAY_ITEM               user play video
        STOP_ITEM               user stop video
        START_GAME              user start game
        * mean no longer ui to create this log in current version
    """
    id = models.AutoField(primary_key=True)
    cpu_id = models.CharField(max_length=50, blank=True, db_index=True)
    action = models.CharField(max_length=30, null=True, blank=True, db_index=True)
    params = models.TextField()
    time = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        app_label = 'curator'


class CuratorStreamUrlLog(models.Model):
    id = models.AutoField(primary_key=True)
    start_at = models.DateTimeField(null=True, blank=True, db_index=True)
    total = models.IntegerField(default=0)
    success = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    cpu_id = models.CharField(max_length=300, blank=True)
    curatorStreamUrl = models.ForeignKey(CuratorStreamUrl, null=True, db_column='curatorStreamUrl_id',
                                         blank=True)  # Field name made lowercase.

    class Meta:
        app_label = 'curator'
        db_table = u'curator_curatorstreamurllog'


class SearchHistoryQuerySet(QuerySet):

    def get_user_hash(self, user):
        if user is None:
            return ''
        return hashlib.sha256(user.username).hexdigest()

    def normalize_keyword(self, keyword):
        return re.sub('\s+', ' ', keyword).strip()

    def get_or_create_new_keyword(self, keyword, user):
        if user.is_anonymous():
            user = None
        user_hash = self.get_user_hash(user)
        keyword = self.normalize_keyword(keyword)
        history = self.filter(keyword=keyword, user_hash=user_hash).first()
        if not history:
            history = self.create(
                keyword=keyword,
                user_hash=user_hash
            )
        return history

    def get_user_history(self, user):
        user_hash = self.get_user_hash(user)
        return self.filter(user_hash=user_hash)


class SearchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    hits = models.IntegerField(default=0)
    # TODO remove user when everything OK
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    user_hash = models.CharField(max_length=64, blank=True, default='')
    objects = SearchHistoryQuerySet.as_manager()

    class Meta:
        app_label = 'curator'

    def adjustHits(self, amountToAdjust):  # ex. 1  2  or  -1
        self.hits = F('hits') + amountToAdjust
        self.save()


class CuratorUserWatchedQuerySet(QuerySet):
    def log(self, playlist_id, user_id):
        if playlist_id:
            watched = self.create(
                curatorPlaylist_id=playlist_id,
                user_id=user_id
            )


class CuratorUserWatched(models.Model):
    id = models.AutoField(primary_key=True)
    curatorPlaylist = models.ForeignKey(CuratorPlaylist)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    objects = CuratorUserWatchedQuerySet.as_manager()

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return "[%s] %s" % (self.curatorPlaylist.channel.name, self.curatorPlaylist.name)


class CuratorUserUnwantedLink(models.Model):
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True)
    link = models.ForeignKey(CuratorLink, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'curator'


class CuratorMirror(models.Model):
    id = models.AutoField(primary_key=True)
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True)
    active = models.BooleanField(default=True)
    youtube_user_id = models.CharField(max_length=256, null=True, blank=True)
    youtube_channel_id = models.CharField(max_length=256, null=True, blank=True)
    youtube_playlist_id = models.CharField(max_length=256, null=True, blank=True)
    instant_add = models.BooleanField(default=True)
    latest_first = models.BooleanField(default=True)
    latest_sync = models.DateTimeField(auto_now_add=True)
    must_publish_after = models.DateTimeField(default=None, null=True, blank=True)
    must_publish_before = models.DateTimeField(default=None, null=True, blank=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return 'Mirror %s' % self.channel.name


class CuratorMirrorRule(models.Model):
    INCLUDE_RULE = 1
    EXCLUDE_RULE = 2
    RULE_CHOICES = (
        (INCLUDE_RULE, 'Include'),
        (EXCLUDE_RULE, 'Exclude'),
    )
    id = models.AutoField(primary_key=True)
    mirror = models.ForeignKey(CuratorMirror)
    keyword = models.CharField(max_length=256, null=True, blank=True, help_text='')
    rule = models.IntegerField(choices=RULE_CHOICES, default=INCLUDE_RULE)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return 'Mirror %s %s %s' % (self.mirror.channel.name, self.get_rule_display(), self.keyword)


class QuestionForum(models.Model):
    id = models.AutoField(primary_key=True)
    playlist = models.ForeignKey(CuratorPlaylist)
    questioner = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(default=timezone.now)
    last_view_by_owner = models.DateTimeField(default=None, null=True, blank=True)
    updated_by_owner = models.DateTimeField(default=None, null=True, blank=True)
    last_view_by_questioner = models.DateTimeField(default=timezone.now)
    updated_by_questioner = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return "[Q] %s" % self.playlist


class QuestionThread(models.Model):
    id = models.AutoField(primary_key=True)
    questionforum = models.ForeignKey(QuestionForum)
    message = models.CharField(max_length=1024)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return "[T] %s" % self.message


class SuggestPlaylistFromQuestion(models.Model):
    id = models.AutoField(primary_key=True)
    questionthread = models.ForeignKey(QuestionThread)
    playlist = models.ForeignKey(CuratorPlaylist)
    created = models.DateTimeField(auto_now_add=True)
    first_watch = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        app_label = 'curator'


DEFAULT_COUNTRY_CODE = 'XX'


class Country(models.Model):
    id = models.AutoField(primary_key=True)
    geoname = models.CharField(max_length=7)
    iso_code = models.CharField(max_length=2)

    def __str__(self):
        return "%s,%s" % (self.iso_code, self.geoname)

    class Meta:
        app_label = 'curator'


class CountryNetwork(models.Model):
    id = models.AutoField(primary_key=True)
    network = models.CharField(max_length=36)
    country = models.ForeignKey(Country, related_name='networks')

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return self.network, self.country_id


class ExtUserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    description = models.TextField(null=True, blank=True, default="")

    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return self.user.username


class UserPhoto(models.Model):
    upload_dir = UploadToDir(settings.ALBUM_PATH)
    id = models.AutoField(primary_key=True)
    photo = models.ImageField(upload_to=upload_dir, verbose_name="photo")
    upload_date = models.DateTimeField(auto_now_add = True)

    class Meta:
        app_label = 'curator'

    def image_(self):
        if self.photo:
            return '<a href="/media/{0}"><img src="/media/{0}"></a>'.format(self.photo)
        return ''
    def image_tag(self):
        if self.photo:
            return u'<img src="%s" width=100 />' % self.photo.url
        return ''
    image_.allow_tags = True
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


class UserPhotoAlbum(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=100, default="")
    photos = models.ManyToManyField(UserPhoto)
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return self.name


class QualityLogResoveSource(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=30, default="")
    ip_hex = models.CharField(max_length=16, default="")
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'curator'

    def __str__(self):
        return self.source
