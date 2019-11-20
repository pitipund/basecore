# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, absolute_import
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http.response import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.utils import translation
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from itertools import chain
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from rest_framework import generics, mixins
from rest_framework.response import Response

from his.penta.curator.gen import gen
from his.penta.channel.utils import PlaylistUtils
from his.penta.curator.forms import *
from his.penta.curator.serializers import ExtUserProfileSerializer
from his.penta.curator.utils import *
from his.penta.showtime.settings import LANGUAGES
from his.penta.showtime.push import pusher
from his.penta.showtime.utils import has_permission, AccessLevel
from his.penta.rating.models import CpuLastLog

playlistutils = PlaylistUtils()
logger = logging.getLogger(__name__)


# ----------profile----------#
class profile_ListView(ListView):
    model = CuratorChannel
    template_name = 'curator/curator_profile.html'

    def get_queryset(self):
        self.user, self.userProfile = utils_get_user_profile_url(self.__dict__['kwargs']['pk'])  # get by request
        if not self.user and not self.userProfile:
            return []
        if self.request.user.id == self.user.id:
            channel = CuratorChannel.objects.filter(user=self.user)
        else:
            channel = CuratorChannel.objects.filter(user=self.user, isPrivate=False)
        for i in channel:
            i.isLive = str(i.isLive)
            i.image = i.real_icon()
            i.url = i.url()
            i.subscribers_number = utils_get_channel_subscribers_number(i)
        #if self.request.user.id:
        #    CuratorLog.objects.create_action_log(self.user, self.request.user, 'W')
        #else:
        #    CuratorLog.objects.create_action_log(self.user, None, 'W')
        return channel

    def get_context_data(self, **kwargs):
        context = super(profile_ListView, self).get_context_data(**kwargs)
        if not context.has_key('curatorchannel_list'):
            return HttpResponseRedirect('/')
        title = self.user.first_name or self.user.username
        context['owner'] = self.user
        context['titlehead'] = title + ' | '
        if self.userProfile:
            context['user_url'] = self.userProfile.user_url()
            context['owner_image'] = self.userProfile.real_image()
            context['owner_display_email'] = str(self.userProfile.isDisplay_email)
        else:
            context['user_url'] = self.user.id
            context['owner_image'] = os.path.join(settings.MEDIA_URL, settings.PROFILE_PATH, 'no_user.png')
            context['owner_display_email'] = str(False)
        context['ogtitle'] = title + "'s profile | "
        context['ogsitename'] = title + "'s profile"
        context['ogpath'] = self.request.path
        context['ogimage'] = context['owner_image']
        return context

    def get(self, request, *args, **kwargs):
        self.user, self.userProfile = utils_get_user_profile_url(self.__dict__['kwargs']['pk'])
        if not self.user:
            raise PermissionDenied()
        if self.request.user.id != self.user.id and not self.request.user.is_staff:
            raise PermissionDenied()
        return super(profile_ListView, self).get(request, *args, **kwargs)


class profile_UpdateView(UpdateView):
    model = User
    form_class = CuratorUserProfile
    template_name = 'curator/curator_profile_update.html'

    def get_context_data(self, **kwargs):
        context = super(profile_UpdateView, self).get_context_data(**kwargs)
        self.user, userProfile = utils_get_user_profile_url(self.__dict__['kwargs']['pk'])
        if userProfile.url_name:
            context['url_name'] = userProfile.url_name  #url only,fill into textinput
        context['image'] = userProfile.real_image()
        context['user'] = self.user
        context['isDisplay_email'] = str(userProfile.isDisplay_email)
        context['user_url'] = userProfile.user_url()
        context['pageheader'] = 'profile'
        return context

    def render_to_response(self, context):
        if not (self.user.id == self.request.user.id):
            utils_curator_save_log("error", "views.py", "profile_UpdateView ",
                                   "Can't open update profile id=%s because you are %s" % (
                                       self.__dict__['kwargs']['pk'], self.request.user.id))
            return render_to_response('404.html', utils_return_404(_("Permission denied."), False),
                                      context_instance=RequestContext(self.request))
        return super(profile_UpdateView, self).render_to_response(context)

    @atomic
    def form_valid(self, form):
        newuser = form.save(commit=False)
        newuser.save()
        url_name_input = self.request.POST.get('url_nameInput')
        url_name_input = ""  # workaround
        if url_name_input.lower() in settings.INVALID_URL_NAME:
            return render_to_response('404.html', utils_return_404(
                _("Profile url: Can not use ") + url_name_input, True),
                                      context_instance=RequestContext(self.request))
        try:
            if int(url_name_input):
                return render_to_response('404.html', utils_return_404(
                    _("Profile url: Can not use numbers only, must have at least one character"), True),
                                          context_instance=RequestContext(self.request))
        except Exception:
            pass
        try:  # update profile
            userProfile = UserProfile.objects.get(user=newuser)

            file_obj = self.request.FILES.get('image_input')
            if file_obj is not None:
                if userProfile.image.name and userProfile.image.name != "uploaded/profile/no_user.png":
                    try:
                        file_name = userProfile.image.name
                        userProfile.image = None
                        userProfile.save()
                        default_storage.delete(file_name)
                    except Exception as e:
                        logger.exception(e.message)
                        pass
                try:
                    image = utils_curator_uploadImage(file_obj)
                except TypeError as e:
                    return HttpResponseBadRequest(e.message)
                userProfile.image.save("%s.jpg" % uuid4(), File(image))

            if url_name_input != "":
                try:
                    isDup = UserProfile.objects.get(url_name=url_name_input[:50])
                except Exception:
                    isDup = False
                if isDup:
                    if isDup.user != userProfile.user:
                        return render_to_response('404.html',
                                                  utils_return_404(_("Profile Url with this Url name already exists."),
                                                                   True),
                                                  context_instance=RequestContext(self.request))
                other = re.sub(r"[a-zA-Z0-9,_]", "", url_name_input)
                if other != "":
                    return render_to_response('404.html',
                                              utils_return_404(_("Profile Url field not allow ") + other, True),
                                              context_instance=RequestContext(self.request))
                userProfile.url_name = url_name_input[:50]
            else:
                userProfile.url_name = None
            userProfile.isDisplay_email = True if self.request.POST.has_key('isDisplay_email') else False
            userProfile.save()
        except Exception:  #create profile

            file_obj = self.request.FILES.get('image_input')

            image = None
            if file_obj is not None:
                try:
                    image = utils_curator_uploadImage(file_obj)
                except TypeError:
                    pass
            if image is None:
                return render_to_response('404.html', utils_return_404(_("image field is required."), True),
                                          context_instance=RequestContext(self.request))
            if url_name_input != "":
                other = re.sub(r"[a-z,A-Z,0-9,_]", "", url_name_input)
                if other != "":
                    return render_to_response('404.html',
                                              utils_return_404(_("Profile Url field not allow ") + other, True),
                                              context_instance=RequestContext(self.request))
                url_name = url_name_input[:50]
            else:
                url_name = None
            userProfile = UserProfile.objects.create(user=newuser, url_name=url_name)
            userProfile.image.save("%s.jpg" % uuid4(), File(image))
        #CuratorLog.objects.create_action_log(newuser, self.request.user, 'E')
        # return redirect('site_profile', userProfile.user_url())
        return redirect('feed:feed_home')


# ----------channel---------- #
class channel_CreateView(CreateView):
    model = CuratorChannel
    form_class = CuratorChannelForm
    template_name = 'curator/curator_channel_create.html'

    def get_context_data(self, **kwargs):
        user, userProfile = utils_get_user_profile_url(self.__dict__['kwargs']['pk'])
        context = super(channel_CreateView, self).get_context_data(**kwargs)
        context['action'] = 'create'
        context['user_url'] = userProfile.user_url()
        utils_set_back_url_to_context('channel_CreateView', self.request, context, ['admin', 'create', 'edit'])
        return context

    @atomic
    def form_valid(self, form):
        if form.is_valid():
            user, userProfile = utils_get_user_profile_url(self.request.user.id)
            try:  # check user and channel name
                channel = CuratorChannel.objects.get(user=user, name=form['name'].value())
                return render_to_response('404.html',
                                          utils_return_404(_("Duplicate channel name ") + form['name'].value(), True),
                                          context_instance=RequestContext(self.request))
            except Exception as e:
                pass

            #tags = utils_get_tag(self.request)
            tags = json.loads(self.request.POST['tags'])
            tags = [tag['name'] for tag in tags]

            if form['url_name'].value() == "":
                url_name = None
            else:
                url_name = form['url_name'].value()
            try:
                # if form['icon'].value() == None and form['icon_url'].value() == "":
                #     return render_to_response('404.html', utils_return_404(_("Please add at least one icon"), True),
                #                               context_instance=RequestContext(self.request))
                new_channel = form.save(commit=False)
                new_channel.user = user
                new_channel.detail = utils_curator_filtertext(form['detail'].value())
                new_channel.pin_queue = None
                new_channel.create_at = timezone.now()
                new_channel.url_name = url_name
                new_channel.save()
                if self.request.user.is_staff:
                    try:
                        p = 1
                        while 'key_result' + str(p) in self.request.POST:
                            if self.request.POST['key_result' + str(p)] != '':
                                CuratorLinkKey.objects.get_or_create(channel=new_channel,
                                                                     name=self.request.POST['key_result' + str(p)])
                            p += 1
                    except:
                        pass
                #CuratorLog.objects.create_action_log(new_channel, user, 'C')
                # Connect Channel to tags
                if new_channel.isLive:
                    tags.append(settings.TAG_LIVE)
                for tag in tags:
                    if tag:
                        t, created = CuratorTag.objects.get_or_create(name=tag)
                        t.curatorChannel.add(new_channel)
                if not new_channel.isLive:
                    t, created = CuratorTag.objects.get_or_create(name=settings.TAG_LIVE)
                    try:
                        t.curatorChannel.get(id=new_channel.id)
                        new_channel.isLive = True
                        new_channel.save()
                    except Exception as e:
                        pass
            except Exception as e:
                utils_curator_save_log("error", "views.py", "channel_CreateView", "%s" % (e))
                return render_to_response('404.html', utils_return_404(e, True),
                                          context_instance=RequestContext(self.request))
            #CuratorLog.objects.create_action_log(new_channel, self.request.user, 'C')
            return HttpResponseRedirect(
                utils_get_back_url('channel_CreateView', self.request, ['admin', 'create', 'edit'], ""))


@login_required
@csrf_exempt
def channel_Subscribe(request):  # REST
    try:
        if 'channelid' not in request.GET:
            raise Exception(_("Can not find channel, Please try again later."))
        if 'type' not in request.GET:
            raise Exception(_("Can not find action, Please try again later."))
        if request.user.is_anonymous():
            raise Exception(_("Can not find user, Please login."))
        _type = request.GET.get('type')
        channel_id = request.GET.get('channelid')
        if channel_id.startswith('live_'):
            status, result = subscript_live_channel(_type, channel_id, request.user)
        else:
            status, result = subscript_curator_channel(_type, int(channel_id), request.user)
    except Exception as e:
        utils_curator_save_log("info", "views.py", "curatorSubscribeChannel", "%s" % e)
        status, result = 0, str(e)
    message = {'status': status, 'msg': result}
    return HttpResponse(json.dumps(message), content_type="application/json")


@login_required
@csrf_exempt
def channel_Delete(request, channel_id):
    try:
        user, userProfile = utils_get_user_profile_url(request.user.id)
        channel = CuratorChannel.objects.get(id=channel_id)
        has_permission(request, channel)
        if not channel.isDefault:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, channel.icon.name))
            except:
                pass
        playlist = CuratorPlaylist.objects.filter(channel=channel)
        # CuratorLog.objects.filter(ref_id__in=playlist.values('id'), category='P').delete()

        # 21/05/15 link must not be deleted
        # for i in playlist:
        #     CuratorLog.objects.create_action_log(i, request.user, 'D')
        #     i.link.all().delete()
        # CuratorLog.objects.filter(category='H',ref_id=channel.id).delete()

        #CuratorLog.objects.create_action_log(channel, request.user, 'D')
        channel.delete()
        CuratorTag.objects.clean_unused_tags()
        return HttpResponseRedirect(utils_get_back_url('channel_Delete', request, ['admin', 'create', 'edit'], ""))
    except CuratorChannel.DoesNotExist:
        utils_curator_save_log("error", "views.py", "curatorRemoveChannel", "id=%s" % (channel_id))
        return render_to_response('404.html', context_instance=RequestContext(request))


@login_required
@csrf_exempt
def channel_checkLive(request, channel_id):  #REST
    try:
        channel = CuratorChannel.objects.get(id=channel_id)
        if channel.isLive:  # Channel is live
            message = {"result": 'true'}
        else:  # change Channel to live must delete all playlist
            playlist = CuratorPlaylist.objects.filter(channel=channel)
            if playlist:
                message = {"result": 'false', "message": _(
                    'Are you sure to change channel setting to Live, your playlist must be deleted?')}
            else:
                message = {"result": 'true'}
        return HttpResponse(json.dumps(message), content_type='application/json')
    except Exception as e:
        utils_curator_save_log("error", "views.py", "curatorCheckLivePlaylist", "id=%s %s" % (channel_id, e))
        message = {"result": 'error', "message": 'Error : %s' % e}
        return HttpResponse(json.dumps(message), content_type='application/json')


@login_required
@csrf_exempt
def channel_DeleteAllPlaylist(request, channel_id):  #REST
    try:
        channel = CuratorChannel.objects.get(id=channel_id)
        has_permission(request, channel)
        playlist = CuratorPlaylist.objects.filter(channel=channel)
        # CuratorLog.objects.filter(ref_id__in=playlist.values('id'), category='P').delete()
        playlist.delete()
        CuratorTag.objects.clean_unused_tags()
        message = {"result": 'true'}
        return HttpResponse(json.dumps(message), content_type='application/json')
    except CuratorChannel.DoesNotExist as e:
        utils_curator_save_log("error", "views.py", "curatorDeleteAllPlaylist", "id=%s %s" % (channel_id, e))
        message = {"result": 'error', "message": 'Error : %s' % (e)}
        return HttpResponse(json.dumps(message), content_type='application/json')


# ----------playlist---------- #
class playlist_CreateView(CreateView):
    model = CuratorPlaylist
    form_class = CuratorPlaylistForm
    template_name = 'curator/curator_playlist_create.html'

    def get_context_data(self, **kwargs):
        context = super(playlist_CreateView, self).get_context_data(**kwargs)
        try:
            channel = CuratorChannel.objects.get(id=self.__dict__['kwargs']['pk'], user=self.request.user)
        except Exception as e:
            utils_curator_save_log("error", "views.py", "playlist_CreateView",
                                   "id=%s %s" % (self.__dict__['kwargs']['pk'], e))
            raise Http404(e)
        context['action'] = 'create'
        context['channel_id'] = channel.id
        context['channel'] = channel.name
        context['isLive'] = channel.isLive
        context['alltags'] = CuratorTag.objects.all()
        utils_set_back_url_to_context('playlist_CreateView', self.request, context, ['admin', 'create', 'edit'])
        return context

    @atomic
    def form_valid(self, form):
        if form.is_valid():
            try:
                channel = CuratorChannel.objects.get(id=self.request.POST['channel_hid'])
            except Exception as e:
                utils_curator_save_log("error", "views.py", "playlist_CreateView",
                                       "id=%s %s" % (self.request.POST['channel_hid'], e))
                return render_to_response('404.html', utils_return_404(e, True),
                                          context_instance=RequestContext(self.request))
            isPass, link, name = utils_get_link_name(self.request)
            tags = utils_get_tag(self.request)
            if not isPass:
                return render_to_response('404.html', utils_return_404(link, True),
                                          context_instance=RequestContext(self.request))
            playlist = CuratorPlaylist.objects.filter(channel=channel)
            new_playlist = form.save(commit=False)
            new_playlist.create_at = timezone.now()
            new_playlist.channel = channel
            new_playlist.save()
            youtube = []
            for l in range(len(link)):
                if re.search('youtube.com', link[l].lower()):
                    youtube.append({"link": link[l], "name": name[l], "index": int(l) + 1})
                elif re.search('dailymotion.com', link[l].lower()):
                    isTrue = utils_curator_create_dailymotion(link[l], name[l], int(l) + 1, new_playlist)
                    if isTrue != True:
                        return render_to_response('404.html', utils_return_404(isTrue, True))
                else:
                    return render_to_response('404.html',
                                              utils_return_404(_("Support only Youtube and Dailymotion"), False))
            if youtube != []:
                isTrue = utils_curator_create_youtube(youtube, new_playlist)
                if isTrue != True:
                    return render_to_response('404.html', utils_return_404(isTrue, False))
            for tag in tags:
                if (tag != ""):
                    try:  #if tag already exists
                        CuratorTag.objects.get(name=tag).curatorPlaylist.add(new_playlist)
                    except:
                        CuratorTag.objects.create(name=tag).save()
                        CuratorTag.objects.get(name=tag).curatorPlaylist.add(new_playlist)
            #CuratorLog.objects.create_action_log(new_playlist, self.request.user, 'C')
            return HttpResponseRedirect(
                utils_get_back_url('playlist_CreateView', self.request, ['admin', 'create', 'edit'], ""))


class playlist_UpdateView(UpdateView):
    model = CuratorPlaylist
    form_class = CuratorPlaylistForm
    template_name = 'curator/curator_playlist_create.html'

    def get_context_data(self, **kwargs):
        context = super(playlist_UpdateView, self).get_context_data(**kwargs)
        try:
            playlist = CuratorPlaylist.objects.get(id=self.__dict__['kwargs']['pk'])
        except Exception as e:
            utils_curator_save_log("error", "views.py", "playlist_UpdateView",
                                   "id=%s %s" % (self.__dict__['kwargs']['pk'], e))
            raise Http404(e)
        url = [{
                'url': playlist.link.url,
                'name': playlist.link.name,
                'img': playlist.link.thumbnail_url
            }]
        context['link'] = json.dumps(url)
        context['channel_id'] = playlist.channel_id
        context['channel'] = playlist.channel.name
        context['isLive'] = str(playlist.channel.isLive)
        context['action'] = 'update'
        context['playlistpk'] = self.__dict__['kwargs']['pk']
        context['selected_tags'] = CuratorTag.objects.filter(curatorPlaylist=self.__dict__['kwargs']['pk'])
        context['alltags'] = CuratorTag.objects.all()
        utils_set_back_url_to_context('playlist_UpdateView', self.request, context,
                                      ignorepages=['admin', 'create', 'edit'])
        return context

    def render_to_response(self, context):
        try:
            curatorPlaylist = CuratorPlaylist.objects.get(id=self.__dict__['kwargs']['pk'])
            if not (curatorPlaylist.channel.user.id == self.request.user.id):
                if not (curatorPlaylist.channel.user.is_staff and self.request.user.is_staff):
                    utils_curator_save_log("error", "views.py", "playlist_UpdateView", "owner %s != user request %s" % (
                        curatorPlaylist.channel.user.id, self.request.user.id))
                    return render_to_response('404.html', utils_return_404(_("Permission denied."), False),
                                              context_instance=RequestContext(self.request))
        except Exception as e:
            utils_curator_save_log("error", "views.py", "playlist_UpdateView",
                                   "id=%s %s" % (self.__dict__['kwargs']['pk'], e))
            return render_to_response('404.html', utils_return_404(_("Can not find playlist."), False),
                                      context_instance=RequestContext(self.request))
        return super(playlist_UpdateView, self).render_to_response(context)

    @atomic
    def form_valid(self, form):
        if form.is_valid():
            isPass, link, name = utils_get_link_name(self.request)
            tags = utils_get_tag(self.request)
            if not isPass:
                return render_to_response('404.html', utils_return_404(link, True),
                                          context_instance=RequestContext(self.request))
            new_playlist = form.save(commit=False)
            try:
                new_playlist.isDefault = CuratorPlaylist.objects.get(id=self.__dict__['kwargs']['pk']).isDefault
            except Exception as e:
                utils_curator_save_log("error", "views.py", "playlist_UpdateView",
                                       "id=%s %s" % (self.__dict__['kwargs']['pk'], e))
                return render_to_response('404.html', utils_return_404(e, True),
                                          context_instance=RequestContext(self.request))
            new_playlist.save()
            isNew, isDel = utils_curator_update_playlist(link, self.__dict__['kwargs'][
                'pk'])  # delete unuse and return new url
            youtube = []
            for j in range(len(link)):
                if link[j] in isNew:  # new for use
                    new_link = CuratorLink.objects.get_video_link(link[j])
                    new_link.create_new_playlist()
                    if re.search('youtube.com', link[j].lower()):
                        youtube.append({"link": link[j], "name": name[j], "index": int(j) + 1})
                    elif re.search('dailymotion.com', link[j].lower()):
                        isTrue = utils_curator_create_dailymotion(link[j], name[j], int(j) + 1, new_playlist)
                        if isTrue != True:
                            return render_to_response('404.html', utils_return_404(isTrue, True),
                                                      context_instance=RequestContext(self.request))
                    elif re.search('rtmp://', link[j].lower()):
                        isTrue = playlistutils.create_link_live_url(self.request, name[j], link[j], 'R', int(j) + 1,
                                                                    new_playlist)
                    elif re.search('.m3u8', link[j].lower()):
                        isTrue = playlistutils.create_link_live_url(self.request, name[j], link[j], 'M', int(j) + 1,
                                                                    new_playlist)
                    elif re.search('rtsp://', link[j].lower()):
                        isTrue = playlistutils.create_link_live_url(self.request, name[j], link[j], 'T', int(j) + 1,
                                                                    new_playlist)
                    else:
                        return render_to_response('404.html',
                                                  utils_return_404(_("Support only Youtube and Dailymotion"), False),
                                                  context_instance=RequestContext(self.request))
                else:  # in db
                    plLink = new_playlist.link.get(url=link[j])
                    plLink.name = name[j]
                    for k in CuratorLinkKey.objects.filter(channel=new_playlist.channel):
                        plLink.name = name[j].lower().replace(k.name.lower(), '').strip()
                    plLink.link_index = int(j) + 1
                    plLink.save()
            if youtube != []:
                isTrue = utils_curator_create_youtube(youtube, new_playlist)
                if isTrue != True:
                    return render_to_response('404.html', utils_return_404(isTrue, False),
                                              context_instance=RequestContext(self.request))
            for i in isDel:  #del not use
                pl = new_playlist.link.filter(url=i)
                CuratorLink.objects.get(id=pl.values('id')).delete()
            #Remove all tags first
            existing_tags = CuratorTag.objects.filter(curatorPlaylist=self.__dict__['kwargs']['pk'])
            for existing_tag in existing_tags:
                existing_tag.curatorPlaylist.remove(new_playlist)
            for tag in tags:  #Connect Channel to tags
                if (tag != ""):
                    try:  #if tag already exists
                        CuratorTag.objects.get(name=tag).curatorPlaylist.add(new_playlist)
                    except:
                        CuratorTag.objects.create(name=tag).save()
                        CuratorTag.objects.get(name=tag).curatorPlaylist.add(new_playlist)
            CuratorTag.objects.clean_unused_tags()
            #CuratorLog.objects.create_action_log(new_playlist, self.request.user, 'E')
            return redirect('channel_channel', new_playlist.channel.id)


@login_required
@csrf_exempt
def playlist_QuickCreate(request):
    if request.POST['name'] and request.POST['link'] and request.POST['channel']:
        try:
            channel = CuratorChannel.objects.get(id=request.POST['channel'])
            curator_link = CuratorLink.objects.get_video_link(request.POST['link'])
            playlist = curator_link.create_new_playlist(channel)
            #CuratorLog.objects.create_action_log(playlist, request.user, 'C')
            if channel.url_name:
                return redirect('channel_channel_name', channel.url_name)
            return redirect('channel_channel', channel.id)
        except Exception as e:
            return render_to_response('404.html', utils_return_404(e, False),
                                      context_instance=RequestContext(request))
    else:
        return render_to_response('404.html', utils_return_404(_("Incomplete information."), False),
                                  context_instance=RequestContext(request))


@login_required
@csrf_exempt
def playlist_Delete(request, id):
    try:
        playlist = CuratorPlaylist.objects.get(id=id)
        channel = CuratorChannel.objects.get(id=playlist.channel.id)
        # CuratorLog.objects.filter(category='P', ref_id=playlist.id).delete()
        #CuratorLog.objects.create_action_log(playlist, request.user, 'D')
        playlist.delete()
        CuratorTag.objects.clean_unused_tags()
        return HttpResponseRedirect(utils_get_back_url('playlist_Delete', request, ['admin', 'create', 'edit'], ""))
    except Exception as e:
        utils_curator_save_log("error", "views.py", "curatorDeletePlaylist", "%s" % (e))
        return render_to_response('404.html', utils_return_404(e, False),
                                  context_instance=RequestContext(request))


def curatorPlaylist_play_or_queue(request, pid):  # REST
    try:
        playlist = CuratorPlaylist.objects.get(id=pid)
        resultId = []
        resultType = []
        resultId.append(playlist.link.video_id)
        resultType.append(playlist.link.video_type)
        message = {"status": 'true', "resultId": resultId, "resultType": resultType, "ptitle": playlist.name}
    except Exception as e:
        utils_curator_save_log("error", "views.py", "curatorPlaylist_play_or_queue", "id=%s %s" % (pid, e))
        message = {"status": 'false'}
    return HttpResponse(json.dumps(message), content_type='application/json')


# ----------notification---------- #
class notification_playlist_ListView(ListView):
    template_name = 'curator/curator_notification_playlist.html'
    paginate_by = 20

    def get_queryset(self):
        self.user, self.userProfile = utils_get_user_profile_url(self.__dict__['kwargs']['pk'])  # get by request
        playlist = CuratorPlaylist.objects.filter(channel__user=self.user, link__isAvailable=False).distinct()
        for i in playlist:
            i.image = i.link.thumbnail_url
            i.channel.isLive = str(i.channel.isLive)
            i.channel.url = i.channel.url()
            i.notAvailable = "%s/%s" % (0, 1)
        return playlist

    def render_to_response(self, context):
        if self.user != self.request.user:
            utils_curator_save_log("error", "views.py", "notification_playlist_ListView ",
                                   "permission denied. owner are %s but you are %s" % (self.user, self.request.user))
            return render_to_response('404.html', utils_return_404(_("Permission denied."), False),
                                      context_instance=RequestContext(self.request))
        return super(notification_playlist_ListView, self).render_to_response(context)

    def get_context_data(self, **kwargs):
        utils_paginate(self)  # Paginate
        context = super(notification_playlist_ListView, self).get_context_data(**kwargs)
        context['page'] = int(self.request.session['page'])
        context['prev_page'] = int(self.request.session['page']) - 1
        context['next_page'] = int(self.request.session['page']) + 1
        context['user_url'] = self.userProfile.user_url()
        utils_set_back_url_to_context('notification_playlist_ListView', self.request, context,
                                      ['admin', 'create', 'edit'])
        return context


@login_required
@csrf_exempt
def notification_link(request, playlist_id):
    try:
        playlist = CuratorPlaylist.objects.get(id=playlist_id, channel__user=request.user)
    except Exception as e:
        return render_to_response('404.html', utils_return_404(_("Can not find playlist."), False),
                                  context_instance=RequestContext(request))
    user, userProfile = utils_get_user_profile_url(request.user.id)
    link = [playlist.link]
    return render(request, 'curator/curator_notification_link.html', {
        "user_url": userProfile.user_url(), "channel": playlist.channel.name, "playlist": playlist,
        "link": link})


@login_required
@csrf_exempt
def notification_link_update(request):
    youtube = []
    for i in range(len(request.POST)):
        if (request.POST.has_key('result' + str(i))):
            loads = json.loads(request.POST['result' + str(i)])
            if loads[0]['url'] != "":
                try:
                    link = CuratorLink.objects.get(id=loads[0]['id'])
                    if re.search('youtube.com', loads[0]['url'].lower()):
                        youtube.append({"link": loads[0]['url'], "name": loads[0]['name'], "curatorLink": link})
                    elif re.search('dailymotion.com', loads[0]['url'].lower()):
                        isOk, result = utils_curator_getInfo_dailymotion(loads[0]['url'])
                        if isOk:
                            utils_update_link(loads[0]['url'], loads[0]['name'], result, link)
                    else:
                        return render_to_response('404.html',
                                                  utils_return_404(_("Support only Youtube and Dailymotion"), False),
                                                  context_instance=RequestContext(request))
                except Exception as e:
                    pass
    isOk = utils_curator_create_youtube(youtube, None)
    try:
        curatorPlaylist = CuratorPlaylist.objects.get(id=request.POST['playlistId_hid'])
        #CuratorLog.objects.create_action_log(curatorPlaylist, request.user, 'E')
        if curatorPlaylist.link.filter(isAvailable=False):
            return redirect('site_notification_link', curatorPlaylist.id)
        elif len(CuratorPlaylist.objects.filter(channel__user=request.user, link__isAvailable=False).distinct()) > 0:
            return redirect('site_notification_playlist', request.user.id)
    except Exception as e:
        utils_curator_save_log("error", "views.py", "notification_link_update", str(e))
    return redirect('channel_home')


@login_required
@csrf_exempt
def notification_Delete(request, playlist_id, link_id):
    try:
        playlist = CuratorPlaylist.objects.get(id=playlist_id, channel__user=request.user)
        link = playlist.link
        if link_id == link.id:
            link.delete()
        if playlist.link:
            #CuratorLog.objects.create_action_log(playlist, request.user, "E")
            if not playlist.link.isAvailable:
                return redirect('site_notification_link', playlist.id)
        else:
            #CuratorLog.objects.create_action_log(playlist, request.user, "D")
            playlist.delete()
        if len(CuratorPlaylist.objects.filter(channel__user=request.user, link__isAvailable=False).distinct()) > 0:
            return redirect('site_notification_playlist', request.user.id)
        else:
            return redirect('channel_home')
    except Exception as e:
        utils_curator_save_log("error", "views.py", "playlist_rest_Delete", "link id=%s %s" % (link_id, e))
        return render_to_response('404.html', utils_return_404(e, False),
                                  context_instance=RequestContext(request))


# ------------Support---------------- #
def render_support_list(version, request, queryset):
    result = []
    for i in queryset.filter(minversion__lte=version):
        tmp_result = {
            "name": i.name,
            "icon": request.build_absolute_uri(i.icon.url),
            "url": i.url,
            "streamUrl": i.pentaStreamUrl(request)
        }
        if i.redirect:
            tmp_result['redirect'] = True
        result.append(tmp_result)
    return result


def get_version(request):
    """Get homerun version from request"""
    try:
        version = int(request.GET.get('version', ''))
        if version == -1:
            version = 142
    except ValueError:
        version = 142
    return version


@csrf_exempt
@dont_cache
def curatorGetOnlineVdo(request):
    result = []
    result.append({"url": "http://www.penta.center/th/", "redirect": True, "streamUrl": None, "name": "Penta center (β)",
                   "icon": "http://www.penta.center/media/images/pentach.jpg"})
    result.append(
        {"url": "http://pentachannel.com/penta_search", "redirect": True, "streamUrl": None, "name": "Penta search",
         "icon": "http://www.penta.center/media/images/pentash.jpg"})
    result.append({"url": "http://www.youtube.com/", "redirect": True, "streamUrl": None, "name": "Youtube",
                   "icon": "http://www.penta.center/media/uploaded/support/youtube.png"})
    result.append({"url": "http://www.dailymotion.com/", "redirect": True, "streamUrl": None, "name": "Dailymotion",
                   "icon": "http://www.penta.center/media/uploaded/support/dailymotion.png"})
    result.append({"url": "http://channel.penta-tv.com/", "redirect": True, "streamUrl": None, "name": "Penta channel",
                   "icon": "http://www.penta.center/media/images/pentach.jpg"})
    response = HttpResponse(json.dumps(result), content_type="application/json")
    response["Access-Control-Allow-Origin"] = "*"
    return response


def get_pentaremote_version(request):
    agent = request.META.get('HTTP_USER_AGENT', '').lower()
    return agent


@csrf_exempt
@dont_cache
def curatorGetSupport(request):
    version = get_version(request)
    curatorSupport = CuratorSupport.objects.filter(enabled=True).order_by("sortkey")
    result = render_support_list(version, request, curatorSupport)
    # backward compatible for PentaRemote for iOS
    device = utils_is_mobile(request)
    is_ios = ('iphone' in device) or ('ipad' in device)
    if ('version' not in request.GET) and is_ios:
        result.append({
            "name": "More Channels",
            "icon": "http://channel.penta-tv.com/media/uploaded/support/pentachannel.png",
            "url": "http://channel.penta-tv.com/apis/support_ios/",
            "streamUrl": None
        })

    remote_info = get_pentaremote_version(request)
    if (remote_info.find("pentaremote ios") > -1):
        os_and_version = remote_info[remote_info.rfind("pentaremote ios"):len(remote_info)]
        if (os_and_version.find("3.3.3") > -1 or os_and_version.find("3.3.4") > -1):
            pass
        else:
            if (result[0]['url'] == "http://www.youtube.com/"):
                result[0]['url'] = settings.MEDIA_URL + 'errata.html'

    response = HttpResponse(json.dumps(result), content_type="application/json")
    response["Access-Control-Allow-Origin"] = "*"
    return response


@csrf_exempt
@dont_cache
def curatorGetLive(request):
    version = get_version(request)
    lang = request.GET.get("lang")
    result = {}
    live_channel = []
    if lang:
        lang = lang.lower().split(',')
    stream_url_item = CuratorStreamUrl.objects.select_related('support').filter(isActive=True, support__enabled=True)
    if lang:
        stream_url_item = stream_url_item.filter(Q(support__languages=None) | Q(support__languages__in=lang))
    stream_url_item = stream_url_item.exclude(streamUrl=None).order_by('support__sortkey', 'order_key', 'id')

    live_collector = {}
    # IMPORTANT: must keep right order_by to maintain correct.

    qos_resolve_source = []
    try:
        qoss = QualityLogResoveSource.objects.all()
        for item in qoss:
            qos = {
                'source': item.source,
                'ip_hex': item.ip_hex,
            }
            qos_resolve_source.append(qos)
    except:
        pass

    country = get_client_country(request)
    idx = 0
    for item in stream_url_item:
        support = item.support
        if support.id not in live_collector:
            live_collector[support.id] = {
                "channel_id": support.channel_id(),
                "name": support.name,
                "icon": request.build_absolute_uri(support.icon.url),
                "channel_number": support.sortkey,
                "stream_url": [],
                "referrer_url": [],
                "primary_link": [],
                "is_thailand": is_thailand(country),
                "is_recorded": support.is_recorded,
                "record_url": support.record_url,
                "record_minute": 4320,
                "allow_oversea": support.allow_oversea
            }
            live_channel.append(live_collector[support.id])
            idx = 0
        live_item = live_collector[support.id]
        live_item["stream_url"].append(item.streamUrl)
        live_item["referrer_url"].append(item.referrerUrl)
        if item.isPrimary:
            live_item["primary_link"].append(idx)
        idx += 1
    result["live_channel"] = live_channel
    result["qos_resolve_source"] = qos_resolve_source
    return HttpResponse(json.dumps(result), status=200, content_type='application/json')


@csrf_exempt
@dont_cache
def curatorGetLiveV2(request):
    version = get_version(request)
    lang = request.GET.get("lang")
    result = {}
    live_channel = []

    if lang:
        lang = lang.lower().split(',')
    stream_url_item = CuratorStreamUrl.objects.select_related('support').filter(isActive=True, support__enabled=True)
    if lang:
        stream_url_item = stream_url_item.filter(Q(support__languages=None) | Q(support__languages__in=lang))
    stream_url_item = stream_url_item.exclude(streamUrl=None).order_by('support__sortkey', 'order_key', 'id')

    live_collector = {}
    # IMPORTANT: must keep right order_by to maintain correct.

    qos_resolve_source = []
    try:
        qoss = QualityLogResoveSource.objects.all()
        for item in qoss:
            qos = {
                'source': item.source,
                'ip_hex': item.ip_hex,
            }
            qos_resolve_source.append(qos)
    except:
        pass

    country = get_client_country(request)
    idx = 0
    for item in stream_url_item:
        support = item.support
        if support.id not in live_collector:
            live_collector[support.id] = {
                "channel_id": support.channel_id(),
                "name": support.name,
                "icon": request.build_absolute_uri(support.icon.url),
                "channel_number": support.sortkey,
                "stream_url": [],
                "primary_link": [],
                "is_thailand": is_thailand(country),
                "is_recorded": support.is_recorded,
                "record_url": support.record_url,
                "record_minute": 4320,
                "allow_oversea": support.allow_oversea
            }
            live_channel.append(live_collector[support.id])
            idx = 0
        live_item = live_collector[support.id]
        live_item["stream_url"].append({
            'url': item.streamUrl,
            'volume': item.volume
        })
        if item.isPrimary:
            live_collector[support.id]["primary_link"].append(idx)
        idx += 1
    result["live_channel"] = live_channel
    result["qos_resolve_source"] = qos_resolve_source
    return HttpResponse(json.dumps(result), status=200, content_type='application/json')


@csrf_exempt
@dont_cache
def curatorGetLiveForMonitorAll(request):
    version = get_version(request)
    lang = request.GET.get("lang")
    result = {}
    live_channel = []
    if lang:
        lang = lang.lower().split(',')
    stream_url_item = CuratorStreamUrl.objects.select_related('support').filter(isActive=True, support__enabled=True)
    if lang:
        stream_url_item = stream_url_item.filter(Q(support__languages=None) | Q(support__languages__in=lang))
    stream_url_item = stream_url_item.exclude(streamUrl=None).order_by('support__sortkey', 'order_key', 'id')

    live_collector = {}
    # IMPORTANT: must keep right order_by to maintain correct.
    idx = 0
    for item in stream_url_item:
        support = item.support
        if support.id not in live_collector:
            live_collector[support.id] = {
                "channel_id": support.channel_id(),
                "name": support.name,
                "icon": request.build_absolute_uri(support.icon.url),
                "channel_number": support.sortkey,
                "stream_url": [],
                "primary_link": [],
            }
            live_channel.append(live_collector[support.id])
            idx = 0
        live_item = live_collector[support.id]
        if 'ppentatoken' in item.streamUrl:
            live_item["stream_url"].append(gen(item.streamUrl.replace('?ppentatoken', '')))
        else:
            live_item["stream_url"].append(item.streamUrl)
        if item.isPrimary:
            live_item["primary_link"].append(idx)
        idx += 1

    playlist_id = CuratorChannel.objects.filter(id__in=settings.SPACIAL_LIVE_CURATOR_CHANNEL) \
        .values_list('curatorplaylist', flat=True)
    curator_playlists = CuratorPlaylist.objects.filter(id__in=playlist_id)
    for item in curator_playlists:
        live = {
            "channel_id": 'live_%d' % item.id,
            "name": item.name,
            "icon": item.link.real_thumbnail(),
            "channel_number": None,
            "stream_url": [item.link.url],
            "primary_link": [item.link.url]
        }
        live_channel.append(live)

    result["live_channel"] = live_channel
    return HttpResponse(json.dumps(result), status=200, content_type='application/json')


@csrf_exempt
@dont_cache
def curatorGetLiveDetail(request, id):
    try:
        curatorSupport = CuratorSupport.objects.get(id=id)
        if curatorSupport.enabled:
            data = curatorSupport.get_live_item(request)
            if len(data['stream_url']) == 0:
                raise Http404
            return HttpResponse(json.dumps(data), status=200, content_type='application/json')
        else:
            raise Http404
    except CuratorSupport.DoesNotExist:
        raise Http404


@csrf_exempt
@dont_cache
def curatorGetLangSupport(request):
    lang = CuratorLanguageSupport.objects.all()
    data = []
    for l in lang:
        data.append({
            'code': l.code,
            'name': l.name,
            'native_name': l.native_name
        })
    return HttpResponse(json.dumps(data), status=200, content_type='application/json')

@csrf_exempt
@dont_cache
def curatorGetCountry(request):
    country = get_client_country(request)
    result = {}
    result['country'] = country
    result['is_thailand'] = is_thailand(country)
    result['ip'] = get_client_ip(request)

    return HttpResponse(json.dumps(result), status=200, content_type='application/json')

@csrf_exempt
@dont_cache
def curatorGetPlaylist(request, id):
    cpuid = request.META.get('HTTP_X_CLIENT_ID', '')
    version = get_version(request)
    channel_id = id.split('_')
    if channel_id[0] == "channel":
        is_live = False
        channel, pin_queue_id, queue, owner = utils_get_support_channel(channel_id[1], limit=200)
    elif channel_id[0] == "live":
        is_live = True
        channel, pin_queue_id, queue, owner = utils_get_support_live(channel_id[1], request, limit=200)
    else:
        return HttpResponse(status=404)
    if channel is False:
        return HttpResponse(status=404)
    # not allow private channel or user save
    if not is_live and (channel.user_save or channel.isPrivate):
        return HttpResponse(status=404)
    if cpuid != "":
        user = User.objects.get_create_penta_user(cpuid)
        if not is_live:
            p, isCreate = PentaSubscript.objects.get_or_create(penta=cpuid, curatorChannel=channel)
        else:
            p, isCreate = PentaSubscript.objects.get_or_create(penta=cpuid, curatorSupport=channel)
        if not isCreate:
            # auto now already done the job when save no need to set update_at
            p.save()
        # CuratorLog.objects.create_apis_log(channel, user, "H")
    result = {"channel_id": "%s_%s" % (channel_id[0], channel.id),
              "pin_queue_id": pin_queue_id,
              "name": channel.name,
              "icon": request.build_absolute_uri(channel.real_icon()),
              "detail": channel.detail if not is_live else '',
              "owner": owner,
              "readonly": 'true',
              "queue": queue}
    if channel_id[0] == "channel":
        if version >= 225:
            result["type"] = 'user_live' if channel.isLive else "queue"
        else:
            result["type"] = "queue"
    else:
        result["type"] = 'live'
    return HttpResponse(json.dumps(result), status=200, content_type='application/json')


@csrf_exempt
@dont_cache
def curatorGetList(request):
    MAX_CHANNEL = 8
    tagList = []
    curatorTag = (CuratorTag.objects.exclude(curatorChannel=None)
                  .filter(show_in_listpage=True).order_by("show_in_listpage_index"))
    for tag in curatorTag:
        channelList = []
        try:
            selectedChannel = tag.channel_show.filter(isPrivate=False).order_by('?')[:MAX_CHANNEL]
            for i in selectedChannel:
                channelList.append({'id': "channel_%s" % i.id, 'name': i.name, 'image': i.real_icon()})
        except:
            pass
        if channelList:
            tagList.append({'tag_id': tag.id, 'tag_name': tag.name, 'tag_name_en': tag.name_en, 'channel': channelList})
    result = {"tag": tagList}
    return HttpResponse(json.dumps(result), status=200, content_type='application/json')


@csrf_exempt
@dont_cache
def curatorGetListMore(request, id):
    access_level = AccessLevel.PENTA
    # access_level = AccessLevel.PENTA if cpuid else AccessLevel.ANY
    base_key = "{0}?{1}#{2}".format(request.path, request.META['QUERY_STRING'], access_level)
    key = "ptvgm_" + base_key
    ret = cache.get(key)
    if not ret:
        tagObj, channel = utils_get_list_more(request, id, access_level=access_level)
        if tagObj is False:
            return HttpResponse(status=404)
        result = {
            'tag_id': tagObj.id,
            'tag_name': tagObj.name,
            'tag_name_en': tagObj.name_en,
            'channel': channel
        }
        ret = json.dumps(result)
        cache.set(key, ret, 300)
    # due to browse by category quite not acculate in new version and cannot detect version then stop log this tag
    # cpuid = request.META.get('HTTP_X_CLIENT_ID', None)
    # if cpuid:
    #     user = User.objects.get_create_penta_user(cpuid)
    #     tagObj = CuratorTag.objects.filter(id=id).first()
    #     if tagObj:
    #         CuratorLog.objects.create_apis_log(tagObj, user, "T")
    return HttpResponse(ret, status=200, content_type='application/json')


# ------------Language---------------- #
@csrf_exempt
def setlang(request, language):
    found = False
    for lang in LANGUAGES:
        if lang[0] == language:
            found = True
            break
    if found:
        translation.activate(language)
        request.session['django_language'] = language
    try:
        referer = request.META['HTTP_REFERER']
    except:
        referer = "/"
    return redirect(referer)


# ------------Admin---------------- #
@login_required
@csrf_exempt
def curatorAdmin(request):
    if request.user.id is None:  # redirect if not login
        return redirect('channel_index')
    if not request.user.is_staff:
        return redirect('channel_index')
    return render(request, 'curator/curator_admin_main.html', {
        "back_url": utils_get_back_url('curatorAdmin', request, ['admin', 'create', 'edit'])})


@login_required
@csrf_exempt
def curatorAdminTag_list(request):
    if request.user.id is None:  # redirect if not login
        return redirect('channel_index')
    if not request.user.is_staff:
        return redirect('channel_index')
    tags = CuratorTag.objects.exclude(curatorChannel=None)
    selected_tags = tags.exclude(show_in_listpage_index=0).order_by('show_in_listpage_index')
    for i in selected_tags:
        i.channel = i.curatorChannel.filter(isPrivate=False)
        for j in i.channel:
            j.isChannel_show = 'False'
            if j in i.channel_show.all():
                j.isChannel_show = 'True'
    deselected_tags = tags.filter(show_in_listpage_index=0).order_by('name')
    for i in deselected_tags:
        i.channel = i.curatorChannel.filter(isPrivate=False)
    result_list = list(chain(selected_tags, deselected_tags))
    return render(request, 'curator/curator_admin_updatetag.html', {
        "tags": result_list,
        "back_url": utils_get_back_url('curatorAdmin', request, ['admin', 'create', 'edit'])
    })


@login_required
@csrf_exempt
def curatorAdminManageChannel(request):
    if request.user.id is None:  #redirect if not login
        return redirect('channel_index')
    if not request.user.is_staff:
        return redirect('channel_index')
    return render(request, 'curator/curator_manage_channel.html')


@login_required
@csrf_exempt
def curatorAdminTag_edit(request):
    if request.user.id == None:
        return redirect('channel_index')
    if not request.user.is_staff:
        return redirect('channel_index')
    for i in CuratorTag.objects.all():  # clear
        i.show_in_listpage = False
        i.show_in_listpage_index = 0
        i.channel_show.clear()
        i.save()
    try:
        j = 1
        while (request.POST.has_key('result' + str(j))):
            loads = json.loads(request.POST['result' + str(j)])
            for k in loads[0]['channel_id'].split(','):
                try:
                    if not CuratorChannel.objects.get(id=k).isPrivate:
                        curatorTag = CuratorTag.objects.get(id=loads[0]['tag_id'],
                                                            curatorChannel=CuratorChannel.objects.get(id=k))
                        curatorTag.channel_show.add(CuratorChannel.objects.get(id=k))
                        curatorTag.show_in_listpage = True
                        curatorTag.show_in_listpage_index = j
                        curatorTag.save()
                except Exception as e:
                    pass
            j += 1
    except Exception as e:
        pass
    return redirect('channel_index')


# ------------Unknow---------------- #
@csrf_exempt
def manual(request):
    return render(request, 'curator/curator_manual.html')


def get_streamurl(url):
    try:
        curator = CuratorStreamUrl.objects.get(streamUrl=url)
    except CuratorStreamUrl.MultipleObjectsReturned:
        curator = CuratorStreamUrl.objects.filter(streamUrl=url)[0]
    except CuratorStreamUrl.DoesNotExist:
        return None
    return curator


@csrf_exempt
def insertRockLog(request):
    logger.debug("insertRockLog called")
    try:
        loads = json.loads(request.POST.get('result', ''))
        cpuId = request.META.get('HTTP_X_CLIENT_ID', '')
        logger.debug( "X-Client-ID: %s", cpuId)
        logs = loads.get('rock')
        with transaction.atomic():
            for i, log in enumerate(logs):
                logger.debug("%d: %s", i, log.get('time'))
                try:
                    RockLog.objects.create(action=log.get('action'), params=json.dumps(log.get('params')), time=log.get('time'),
                                           cpu_id=cpuId)
                except Exception as e:
                    logger.exception(e.message)
            # transaction.commit()
    except:
        return HttpResponseBadRequest("Bad request")
    return HttpResponse("insert rock log done")


def validate_request(request, required=['cpu_id', 'url', 'start_at', 'result']):
    loads = json.loads(request.POST.get('result', ''))
    for k in required:
        if k not in loads:
            raise ValueError
    return [loads[k] for k in required]


@csrf_exempt
def insertLog(request):
    try:
        cpu_id, url, start_at, result = validate_request(request)
    except ValueError:
        return HttpResponseBadRequest("Bad request")
    if not start_at:
        return HttpResponseBadRequest("No timestamp when it start")
    curator = get_streamurl(url)
    if curator:
        updateCpuLastLog(cpu_id, start_at, curator)
        try:
            c = CuratorStreamUrlLog.objects.get(start_at=start_at, cpu_id=cpu_id, curatorStreamUrl=curator)
            c.total += 1
            c.success += int(result)
            c.save()
        except CuratorStreamUrlLog.MultipleObjectsReturned:
            cs = CuratorStreamUrlLog.objects.filter(start_at=start_at, cpu_id=cpu_id, curatorStreamUrl=curator)
            c0 = cs.first()
            for c in cs[1:]:
                c0.success += c.success
                c0.total += c.total
                c0.duration += c.duration
                c.delete()
            c0.total += 1
            c0.success += int(result)
            c0.save()
        except CuratorStreamUrlLog.DoesNotExist:
            CuratorStreamUrlLog.objects.create(start_at=start_at, cpu_id=cpu_id, curatorStreamUrl=curator, total=1,
                                               success=int(result), duration=0)
        return HttpResponse("insertLog done <br>" + cpu_id + " " + url + " " + start_at + " " + result)
    else:
        logger.warning('cannot insert log, %s does not exists' % url)
        return HttpResponseNotFound("URL does not exists " + url)


@csrf_exempt
def updateDuration(request):
    try:
        cpu_id, url, start_at, duration = validate_request(request,
                                                           required=['cpu_id', 'url', 'start_at', 'duration'])
    except ValueError:
        return HttpResponseBadRequest("Bad request")
    if not start_at:
        return HttpResponseBadRequest("No timestamp when it start")
    curator = get_streamurl(url)
    if curator:
        updateCpuLastLog(cpu_id, timezone.now(), curator)
        try:
            c = CuratorStreamUrlLog.objects.get(start_at=start_at, cpu_id=cpu_id, curatorStreamUrl=curator)
            c.duration += int(duration)
            c.save()
        except CuratorStreamUrlLog.MultipleObjectsReturned:
            cs = CuratorStreamUrlLog.objects.filter(start_at=start_at, cpu_id=cpu_id, curatorStreamUrl=curator)
            c0 = cs.first()
            for c in cs[1:]:
                c0.success += c.success
                c0.total += c.total
                c0.duration += c.duration
                c.delete()
            c0.duration += int(duration)
            c0.save()
        except CuratorStreamUrlLog.DoesNotExist:
            CuratorStreamUrlLog.objects.create(start_at=start_at, cpu_id=cpu_id, curatorStreamUrl=curator, total=1,
                                               success=1, duration=int(duration))
        if start_at is None:
            start_at = ''
        return HttpResponse("updateDuration done <br>" + cpu_id + " " + url + " " + start_at + " " + duration)
    else:
        logger.warning('cannot update log, %s does not exists' % url)
        return HttpResponseNotFound("URL does not exists " + url)


def updateCpuLastLog(cpu_id, start_at, curatorStreamUrl):
    curator_support = curatorStreamUrl.support
    try:
        row = CpuLastLog.objects.get(cpu_id=cpu_id)
        row.latest_log = start_at
        row.channel = curator_support
        row.save()
    except Exception as e:
        logger.error(e)
        CpuLastLog.objects.create(cpu_id=cpu_id, latest_log=start_at, channel=curator_support)


@csrf_exempt
def getChannel(request):
    data = json.loads(request.POST.get('result', "[]"))
    try:
        channel = data[0]['channel']
    except IndexError:
        return HttpResponseBadRequest("invalid result")
    c_list = CuratorStreamUrl.objects.filter(support__name=channel).values('streamUrl')
    return HttpResponse("getChannel done " + str(c_list))


@staff_member_required
def curatorAdmin_push_changes(request):
    if request.GET.get('item') == 'live_all':
        pusher.update_live_all()
        messages.success(request, 'Pushed changes to PentaTV successfully')
    else:
        messages.error(request, 'Unknown message type')
    return redirect('/admin/curator/curatorsupport/')


def validate_push_form(request):
    form = {}
    dialog_methods = ['update', 'cancel']
    fields = (
        ('push_type', ['toast', 'dialog', 'marquee']),
        ('target', ['all', 'cpuid']),
        ('cpuid', lambda x: len(x) > 0 if form['target'] == 'cpuid' else True),
        ('toast_text', lambda x: len(x) > 0 if form['push_type'] == 'toast' else True),
        ('marquee_text', lambda x: len(x) > 0 if form['push_type'] == 'marquee' else True),
        ('marquee_duration', lambda x: int(x) > 0 if form['push_type'] == 'marquee' else True),
        ('dialog_text', lambda x: len(x) > 0 if form['push_type'] == 'dialog' else True),
        ('dialog_choice1', lambda x: len(x) > 0 if form['push_type'] == 'dialog' else True),
        ('dialog_choice2', lambda x: len(x) > 0 if form['push_type'] == 'dialog' else True),
        ('method_choice1', lambda x: x in dialog_methods if form['push_type'] == 'dialog' else True),
        ('method_choice2', lambda x: x in dialog_methods if form['push_type'] == 'dialog' else True),
    )
    for key, predicate in fields:
        form[key] = request.POST.get(key, "")
        if type(predicate) == list:
            if form[key] not in predicate:
                logger.error('error from %s', key)
                raise ValueError
        else:
            if not predicate(form[key]):
                logger.error('error from %s', key)
                raise ValueError
    return form


@csrf_exempt
def preview_snapshot(request):
    url = request.GET.get('url', "")
    vid = int(request.GET.get('v', "0"))
    pic = int(request.GET.get('n', "1"))
    redirect_uri = "/media/snapshot/"

    if vid:
        curator_link = get_object_or_404(CuratorLink, pk=vid)
    elif url:
        curator_link = get_object_or_404(CuratorLink, url=url)
    else:
        raise Http404()

    if not curator_link.snapshot_url:
        raise Http404("No previews for this video")
    redirect_uri += curator_link.snapshot_url + "/" + str(pic).zfill(2) + ".jpg"
    return HttpResponseRedirect(redirect_uri)


@staff_member_required
def curatorAdmin_push_messages(request):
    if request.method == 'POST':
        try:
            form = validate_push_form(request)
            target = ("cpu_%s" % form['cpuid']) if form['target'] == 'cpuid' else 'all'
            if form['push_type'] == 'toast':
                pusher.push_toast(form['toast_text'], target=target)
                messages.success(request, u"Push toast '%s' successful" % form['toast_text'])
            elif form['push_type'] == 'marquee':
                duration = int(form['marquee_duration']) * 1000
                pusher.push_marquee(form['marquee_text'], duration, target=target)
                messages.success(request, u"Push marquee '%s' successful" % form['marquee_text'])
            elif form['push_type'] == 'dialog':
                pusher.push_dialog(form['dialog_text'],
                                   (form['dialog_choice1'], form['dialog_choice2']),
                                   (form['method_choice1'], form['method_choice2']),
                                   target=target)
                messages.success(request, u"Push dialog '%s' successful" % form['dialog_text'])
        except ValueError:
            messages.warning(request, 'Invalid input')
    return render(request, 'curator/curator_admin_push_message.html')

@staff_member_required
def curatorAdmin_emails(request):
    user = request.user

    channels = list(CuratorChannel.objects.filter(user_save=False, user_share=False, user__is_staff=True))
    channels = sorted(channels, key=lambda x: x.followers.count(), reverse=True)

    return render(request, 'curator/curator_admin_emails.html', {'channels': channels})


class ExtProfileRetrieveUpdate(mixins.RetrieveModelMixin, generics.GenericAPIView):
    "1"
    serializer_class = ExtUserProfileSerializer
    queryset = ExtUserProfile.objects.all()

    #################### Custom mixin
    def retrieve(self, request, *args, **kwargs):
        # instance = self.get_object() # drf get instance from pk
        user = self.request.user
        instance, created = ExtUserProfile.objects.get_or_create(user=user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = self.request.user
        instance, created = ExtUserProfile.objects.get_or_create(user=user)
        # instance = self.get_object() # drf get instance from pk
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    ##################### Custom Allow method

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ExtProfileRetrieveUpdateOrigi(generics.RetrieveUpdateAPIView):
    "2"
    serializer_class = ExtUserProfileSerializer
    queryset = ExtUserProfile.objects.all()


# class UserPhotoAlbumList(generics.ListCreateAPIView):
#     """
#
#     """
#     serializer_class = UserPhotoAlbumSerializer
#     queryset = Appointment.objects.all()
