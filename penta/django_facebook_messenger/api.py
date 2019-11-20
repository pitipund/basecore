from __future__ import absolute_import, unicode_literals, print_function

import json
import mimetypes
import requests
import hmac
import hashlib

from django.conf import settings
from django.core.cache import cache


class FacebookMessengerException(Exception):
    """
    Exception from Facebook Messenger API
    Contains json as message, can be extracted with `json.loads()`
    """
    pass


def get_page(page_name):
    """
    Get page dict from settings
    :param page_name: Name of page configured in settings
    :return: page dict
        {'id': '<id>',
         'name': '<page_name>',
         'token': '<token>}
    """
    pages = settings.FACEBOOK_PAGE_ACCESS
    return next((page for page in pages if page["name"] == page_name), None)


def get_app_access_token():
    """
    Get Facebook app access token and store in cache if valid
    :return:
        {'access_token': '571837776208476|SwOdya5wGnLt-YEBWf9YeszWCnE',
         'token_type': 'bearer'}
    """
    access_token = cache.get('FbMsgAPI_AppAccessToken')
    if access_token:
        return access_token
    params = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'grant_type': 'client_credentials',
    }
    res = requests.get('https://graph.facebook.com/v2.12/oauth/access_token',
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    access_token = res.json()
    cache.set('FbMsgAPI_AppAccessToken', access_token, 86400)  # cache for one day
    return access_token


def get_page_access_token(page_name):
    """
    Get new page token, you can always use old token in the settings.
    So this function maybe useless, I don't know why I implemented this though.
    :param page_name: Name of page configured in settings
    :return:
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    access_token = cache.get('FbMsgAPI_PageAccessToken_%s' % page_name)
    if access_token:
        return access_token
    params = {
        'access_token': page['token'],
        'fields': 'access_token'
    }
    res = requests.get('https://graph.facebook.com/v2.12/me',
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    access_token = res.json()
    cache.set('FbMsgAPI_PageAccessToken_%s' % page_name, access_token, 86400)  # cache for one day
    return access_token


def get_inbox_list(page_name, before=None, after=None, limit=50):
    """
    This function will return generator (can be iterated with `for loop` or using `next()`).
    If you want only one iteration result, you can call `get_inbox_list('<page_name>').next()`

    With this function you can get `user_id` from `['sender']['data'][0]['id']`

    Due to Graph API paging system you cannot direct specific page number.
    But you can use `node id` in `before` and `after` point to specific page.
    You can specific only one of `before` or `after` if given both `after` will be used.

    [more info about paging][https://developers.facebook.com/docs/graph-api/using-graph-api#paging]

    :param page_name: Name of page configured in settings
    :param before: Facebook `before` paging node id
    :param after: Facebook `after` paging node id
    :param limit: Limit output nodes count (default 50)
    :return: dict
        {
            "data": [
                {
                    "id": "<inbox id>",
                    "can_reply": <bool whether or not you can sent back message>,
                    "message_count": <int>,
                    "unread_count": <int>,
                    "sender": {
                        "data": [
                            {
                                "name": "<sender name>",
                                "email": "email of sender (useless)",
                                "id": "<sender app user id>"
                            },
                            {
                                "name": "<receiver name>",
                                "email": "email of receiver (useless)",
                                "id": "<receiver app user id>"
                            }
                        ]
                    },
                    "is_subscribed": <bool user subscribed to your fb page>,
                    "updated_time": "<iso time>"
                }, ...
            ],
            "paging": {
                "cursors": {
                    "before": "",
                    "after": "",
                },
                "previous": "<url>"  # this line only appear when it has previous page, useless
                "next": "<url>"  # this line only appear when it has next page, useless
            }
        }
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    params = {
        'access_token': page['token'],
        'fields': 'id,can_reply,message_count,updated_time,'
                  'unread_count,senders,is_subscribed',
        'limit': limit,
    }
    if after:
        params['after'] = after
    elif before:
        params['before'] = before
    res = requests.get('https://graph.facebook.com/v2.12/me/conversations',
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.json())
    data = res.json()
    next_page = data['paging'].get('next', None) if 'paging' in data else None
    yield data

    while next_page:
        res = requests.get(next_page)
        if res.status_code >= 400:
            raise FacebookMessengerException(res.content)
        data = res.json()
        next_page = data['paging'].get('next', None) if 'paging' in data else None
        yield data


def get_inbox(page_name, inbox_id=None, psid=None, user_id=None):
    """
    Get inbox detail (like get_inbox_list but only one inbox).
    You can use either inbox_id or user_id or psid to query.
    :param page_name: Name of page configured in settings
    :param inbox_id: inbox id
    :param psid: user's page scope id
    :param user_id: user's app id
    :return: { "id": <inbox_id>,
               "can_reply": <bool>,
               "message_count": <int>,
               "updated_time": "<iso_datetime>,
               "unread_count": <int>,
               "senders": {
                   "data": [
                       {
                           "name": "<sender name>",
                           "email": "email of sender (useless)",
                           "id": "<sender app user id>"
                       },
                       {
                           "name": "<receiver name>",
                           "email": "email of receiver (useless)",
                           "id": "<receiver app user id>"
                       }
                   ]
               },
               "is_subscribed": <bool>
             }
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    params = {
        'access_token': page['token'],
        'fields': 'id,can_reply,message_count,updated_time,'
                  'unread_count,senders,is_subscribed',
    }
    if inbox_id is None:
        if user_id is None:
            if psid is not None:
                user_id = convert_psid_to_user_id(page_name, psid)['id']
                if not user_id:
                    raise FacebookMessengerException('Invalid `psid`')
            else:
                raise FacebookMessengerException('Need `inbox_id`, `user_id`, or `psid`')

        # search for inbox
        for l in get_inbox_list(page_name):
            inbox_list = l['data']
            for inbox in inbox_list:
                senders_data = inbox['senders']['data']
                for sender in senders_data:
                    if sender['id'] == user_id:
                        return inbox
        raise FacebookMessengerException('{"error": {"message": "inbox not found"}}')

    res = requests.get('https://graph.facebook.com/v2.12/%s' % inbox_id,
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.json())
    data = res.json()
    return data


def get_messages(page_name, inbox_id, before=None, after=None, limit=25):
    """
        This function will return all messages in the inbox (bidirectional)
        with given `inbox_id`, newest message first.
        You can get `inbox_id` from `get_inbox_list('<page_name>')`

        Due to Graph API paging system you cannot direct specific page number.
        But you can use `node id` in `before` and `after` point to specific page.
        You can specific only one of `before` or `after` if given both `after` will be used.

        [more info about paging][https://developers.facebook.com/docs/graph-api/using-graph-api#paging]

        :param page_name: Name of page configured in settings
        :param inbox_id: id od inbox
        :param before: Facebook `before` paging node id
        :param after: Facebook `after` paging node id
        :param limit: Limit output nodes count (default 50)
        :return: dict
            {
                "data": [
                    {
                        "created_time": "<iso time>",
                        "message": "<string>",
                        "from": {
                            "name": "<username or page>",
                            "email": "<email no use>",
                            "id": "<user id or page id>"
                        }
                        "id": "<message id>"
                    },
                    {
                        "created_time": "<iso time>",
                        "sticker": "<url>"
                        "message": "",
                        ...
                    },
                    {
                        "created_time": "<iso time>",
                        "message": "",
                        "attachments": {
                            data: [
                                {
                                    "mime_type": "image/jpeg",
                                    "image_data": {
                                        "width": <int>,
                                        "height": <int>,
                                        "max_width": <int>,
                                        "max_height": <int>,
                                        "url": "<url>",
                                        "preview_url": "<url>",
                                        "image_type": <int>,
                                        "render_as_sticker": <bool>
                                    },
                                    "id": "<useless>"
                                }
                            ], ...useless data...
                        },
                        ...
                    },
                    {
                        "created_time": "<iso time>",
                        "message": "",
                        "attachments": {
                            data: [
                                {
                                    "mime_type": "video/mp4",
                                    "video_data": {
                                        "width": <int>,
                                        "height": <int>,
                                        "length": <int in sec>,
                                        "video_type": <int>,
                                        "url": "<video url>",
                                        "preview_url": "<snapshot url>",
                                        "rotation": 0
                                    },
                                    "id": "1714935711901579"
                                }
                            ], ...useless data...
                        },
                        ...
                    },
                    {
                        "created_time": "<iso time>",
                        "message": "",
                        "attachments": {
                            data: [
                                {
                                    "file_url": "<file url>",
                                    "id": "1744885225573294",
                                    "mime_type": "application/pdf"}
                            ], ...useless data...
                        },
                        ...
                    }
                    ...
                ],
                "paging": {
                    "cursors": {
                        "before": "",
                        "after": "",
                    },
                    "previous": "<url>"  # this line only appear when it has previous page, useless
                    "next": "<url>"  # this line only appear when it has next page, useless
                }
            }
        """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    params = {
        'access_token': page['token'],
        'fields': 'created_time,message,sticker,from,'
                  'attachments{mime_type,file_url,image_data,video_data}',
        'limit': limit,
    }
    if after:
        params['after'] = after
    elif before:
        params['before'] = before
    res = requests.get('https://graph.facebook.com/v2.12/%s/messages' % inbox_id,
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.json())
    data = res.json()
    next_page = data['paging'].get('next', None) if 'paging' in data else None
    yield data

    while next_page:
        res = requests.get(next_page)
        if res.status_code >= 400:
            raise FacebookMessengerException(res.content)
        data = res.json()
        next_page = data['paging'].get('next', None) if 'paging' in data else None
        yield data


def get_page_message_tags(page_name):
    """
    Get all tags, available for post_messages()

    [more about message tags]
    [https://developers.facebook.com/docs/messenger-platform/send-messages/message-tags]

    :param page_name: Name of page configured in settings
    :return: list of dict
    [{'description': '<tag description>',
      'tag': '<tag name>'},
      ...]
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    params = {
        'access_token': page['token']
    }
    res = requests.get('https://graph.facebook.com/v2.12/page_message_tags', params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    data = res.json()['data']
    return data


def post_messages(page_name, psid=None, message='', user_id=None, tag=None):
    """
    Post a message to user with `psid`
    available `tag` can be got from `get_page_message_tags()`

    :param page_name: Name of page configured in settings
    :param psid: Page scope user id
    :param message: raw text message
    :param user_id: application scope user id
    :param tag: message with message tag, get tag from `get_page_message_tags()`
    :return:
    on success:
    {'message_id': 'mid.$cAADgTuosnwNoJZf8N1h9FKzlzdl5',
     'recipient_id': '<psid>'}

    on error (FacebookMessengerException raised):
    {"error":{
        "message":"(#100) Parameter error: You cannot send messages to this id",
        "type":"OAuthException",
        "code":100,
        "fbtrace_id":"C1zKTxHv2DO"
    }}
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    params = {
        'access_token': page['token'],
    }

    if psid is None and user_id is not None:
        psid_data = convert_user_id_to_psid(page_name, user_id)
        if psid_data is None:
            raise FacebookMessengerException('"error":{"message":"Cannot found user '
                                             'with this id in this page"}')
        psid = psid_data['id']

    data = {
        'messaging_type': 'RESPONSE',
        'recipient': {
            'id': psid,
        },
        'message': {
            'text': message
        }
    }
    if tag:
        data['messaging_type'] = 'MESSAGE_TAG'
        data['tag'] = tag

    res = requests.post('https://graph.facebook.com/v2.12/me/messages',
                        params=params, json=data)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    return res.json()


def post_media(page_name, psid=None, file_path=None, file_url=None, user_id=None, tag=None):
    """
    Post a media message to user with `psid`

    I think this should work for every type of files.
    The visualization on message box will depended on MIME type of file.
    Basically, Facebook only support 'video', 'audio' and 'image'
    for other types they will be labeled as 'file'

    You can specific `file_url` for upload performance, depend on where did you upload from.
    If you upload from server, `file_url` may be better option.
    But `file_path`, still, has to be given.

    available `tag` can be got from `get_page_message_tags()`

    :param page_name: Name of page configured in settings
    :param psid: Page scope user id
    :param file_path: path of file to send
    :param file_url: url of file to send (optional)
    :param user_id: application scope user id
    :param tag: message with message tag, get tag from `get_page_message_tags()`
    :return: `attachment_id` can be used for other occasion
        {'attachment_id': '209632692952581',
         'message_id': 'mid.$cAADgTrNHAEBoLBT57Fh-s-w1x3u4',
         'recipient_id': '1665249260180665'}
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
    params = {
        'access_token': page['token'],
    }

    if psid is None and user_id is not None:
        psid_data = convert_user_id_to_psid(page_name, user_id)
        if psid_data is None:
            raise FacebookMessengerException('"error":{"message":"Cannot found user '
                                             'with this id in this page"}')
        psid = psid_data['id']

    if file_url:
        mime_type = mimetypes.guess_type(file_url)[0]
    elif file_path:
        mime_type = mimetypes.guess_type(file_path)[0]
    else:
        raise TypeError('`file_url` or `file_path` have to be given')

    file_type = None
    if mime_type is not None:
        file_type = mime_type.split('/')[0]
    if file_type not in ['image', 'audio', 'video', 'file']:
        file_type = 'file'

    attachment = {
        'attachment': {
            "type": file_type,
            "payload": {
                "is_reusable": True
            }
        }
    }
    if file_url:
        attachment['attachment']['payload']['url'] = file_url

    data = {
        'messaging_type': 'RESPONSE',
        'recipient': json.dumps({
            'id': psid,
        }),
        'message': json.dumps(attachment)
    }
    if tag:
        data['messaging_type'] = 'MESSAGE_TAG'
        data['tag'] = tag

    if file_url:
        res = requests.post('https://graph.facebook.com/v2.12/me/messages',
                            params=params, data=data)
    elif file_path:
        f = open(file_path, 'r')
        res = requests.post('https://graph.facebook.com/v2.12/me/messages',
                            params=params, data=data, files={'file': (file_path.split('/')[-1],
                                                                      f, mime_type)})
    else:
        raise Exception('You should not be here!')
    print(res.request.headers)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    return res.json()


def convert_psid_to_user_id(page_name, psid):
    """
    Converts page-scoped user id (psid) to app-scoped user id.
    Raise `FacebookMessengerException` if no `psid` found in page.
    :param page_name: Name of page configured in settings
    :param psid: Page scope user id
    :return:
    {'app': {
        'category': 'Entertainment',
        'id': '571837776208476',
        'link': 'https://apps.facebook.com/pentaid/',
        'name': 'PentaCenter',
        'namespace': 'pentaid'},
     'id': '100001555003418'}
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)

    data = cache.get('FbMsgAPI_PSID2UID_%s' % psid)
    if data is not None:
        return data

    proof = hmac.new(settings.FACEBOOK_APP_SECRET,
                     page['token'],
                     hashlib.sha256).hexdigest()
    params = {
        'app': settings.FACEBOOK_APP_ID,
        'access_token': page['token'],
        'appsecret_proof': proof
    }
    res = requests.get('https://graph.facebook.com/v2.12/%s/ids_for_apps' % psid,
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    data = res.json()['data']
    if data:
        cache.set('FbMsgAPI_PSID2UID_%s' % psid, data[0], 86400)
        return data[0]
    return None


def convert_user_id_to_psid(page_name, user_id):
    """
    Converts app-scoped user id to page-scoped user id (psid).
    Return `None` if user hasn't ever interacted with page before
    :param page_name: Name of page configured in settings
    :param user_id: App-scoped user id
    :return:
    {'id': '1665249260180665',
     'page': {
        'id': '205324643383386',
        'name': 'Penta TV Developer'}
    }
    """
    page = get_page(page_name)
    if not page:
        raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)

    data = cache.get('FbMsgAPI_UID2PSID_%s' % user_id)
    if data is not None:
        return data

    access_token = get_app_access_token()['access_token'].encode('ascii')
    proof = hmac.new(access_token,
                     settings.FACEBOOK_APP_ID,
                     hashlib.sha256).hexdigest()
    params = {
        'page': page['id'],
        'access_token': access_token,
        'appsecret_proof': proof
    }
    res = requests.get('https://graph.facebook.com/v2.12/%s/ids_for_pages' % user_id,
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    data = res.json()['data']
    if data:
        cache.set('FbMsgAPI_UID2PSID_%s' % user_id, data[0], 86400)
        return data[0]
    return None


def get_user_data(uid, page_name=None):
    """
    Gets detail of user. The detail you got will depended on permission you got from users.
    When you call this function with `psid` and `page_name`, this function will try
    to convert `psid` to app-scoped user id (app will get more permission than pages anyway)

    :param uid: `id` of user. If `psid` is given you have to specific `page_name`
    :param page_name: if `page_name` is not given, this function will use application token
    :return:
    {
        "name": "<full name>",
        "id": "<user id or psid>"
        "gender": "<male|female (optional)>"
        "email": "<user email (optional)>"
    }
    (optional) will appear or not, depended on app permission
    """
    params = {
        'access_token': settings.FACEBOOK_APP_ACCESS_TOKEN,
        'fields': 'name,email,devices,age_range,gender',
    }
    if page_name:
        page = get_page(page_name)
        if not page:
            raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
        user_id = convert_psid_to_user_id(page_name, uid)
        if user_id is None:
            params['access_token'] = page['token']
        else:
            uid = user_id['id']
    res = requests.get('https://graph.facebook.com/v2.12/%s' % uid,
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    return res.json()


def get_user_pic(uid, page_name=None, width=250, height=250, pic_only=False):
    """
    Gets profile picture of user. Use width and height to change picture size but
    the returned picture size will not be exact input width and height.
    You have to get exact size from return dict

    When you call this function with `psid` and `page_name`, this function will try
    to convert `psid` to app-scoped user id (app will get more permission than pages anyway)

    :param uid: `id` of user. If `psid` is given you have to specific `page_name`
    :param page_name: if `page_name` is not given, this function will use application token
    :param width: estimate width
    :param height: estimate height
    :param pic_only: if `True` return picture url only
    :return:
    {
        "height": 314,
        "is_silhouette": false,
        "url": "https://scontent.xx.fbcdn.net/v/t1.0-1/c23.1.314.314/p320x320/10277559_1410902009186124_2253247070596150929_n.jpg?_nc_cat=0&oh=6dd9607bfbe0c6ce53c20fa61837b65e&oe=5B44E2CC",
        "width": 314
    }
    """
    if pic_only:
        return 'https://graph.facebook.com/v2.12/{}/picture?width={}&height={}'.format(uid, width, height)
    params = {
        'access_token': settings.FACEBOOK_APP_ACCESS_TOKEN,
        'width': width,
        'height': height,
        'redirect': False,
    }
    if page_name:
        page = get_page(page_name)
        if not page:
            raise FacebookMessengerException('No `%s` in FACEBOOK_PAGE_ACCESS' % page_name)
        user_id = convert_psid_to_user_id(page_name, uid)
        if user_id is None:
            params['access_token'] = page['token']
        else:
            uid = user_id['id']
    res = requests.get('https://graph.facebook.com/v2.12/%s/picture' % uid,
                       params=params)
    if res.status_code >= 400:
        raise FacebookMessengerException(res.content)
    return res.json()['data']
