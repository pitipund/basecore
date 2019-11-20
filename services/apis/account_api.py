"""
Name:     AccountAPI
Version:  0.2
Modified: May 22, 2013
Maintainer: Natt Piyapramote <natt@thevcgroup.com>

This class provide API for accounts.thevcgroup.com.

1. Create user (email, password), and automatically activate account
2. Check if user exists
3. Create user (login url, email, password) and automatically generate CAS token

It requires 'requests' library:
   $ sudo pip install requests

"""
import requests
import json
import traceback
import logging

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import send_mail

from his.penta.pentacenter.models import Device, App
from his.penta.curator.models import User as PentaChannelUser
from rest_framework.authtoken.models import Token

from his.users.admin import ApplicationDefaultRole
from his.users.models import UserProfile, User, MobileDevice, APIToken

logger = logging.getLogger(__name__)


class AccountAPI(object):
    API_URL = "https://accounts.thevcgroup.com/apis/v1/"
    FB_REGISTER_URL = "https://accounts.thevcgroup.com/apis/register_by_token/facebook/"
    API_USER = "pentachannel"
    API_KEY = "f6176e857b7f99c91609f2c618114bff7f8b92ef"

    ACTION_NEW_USER = "new_user/"
    ACTION_NEW_USER_FACEBOOK = "new_facebook_user/"
    ACTION_GET_CAS_TOKEN = "get_cas_token/"

    def post(self, action, data):
        return requests.post("%s%s" % (self.API_URL, action),
                             data=json.dumps(data),
                             headers={'Content-Type': 'application/json',
                                     'Authorization': 'ApiKey %s:%s' % (self.API_USER, self.API_KEY)},
                             verify=False)

    def create_user(self, email, password, first_name=None, last_name=None):
        payload = {
            "email": email,
            "password": password,
        }
        if first_name:
            payload['first_name'] = first_name
        if last_name:
            payload['last_name'] = last_name

        result = self.post(self.ACTION_NEW_USER, payload)
        if result.status_code == 201:
            return True, 'Successfully created'
        elif result.status_code == 401:
            return False, 'Authentication failed (Invalid API_KEY or API_USER)'
        elif result.status_code == 400:
            if 'UserExists' in result.text:
                return False, 'User with this email is already exists'
        if result.text != "":
            return False, result.text
        return False, 'Unknown error'

    def create_facebook_user(self, access_token, unique_id, time, device_type,
                             fb_id, fb_username, fb_firstname, fb_lastname, fb_email,
                             fb_avatarUrl, fb_expire=None, pUser=None, device_token='', app=None):
        # Create PentaChannel User
        try:
            if isinstance(device_type, str):
                device_type = device_type.strip().lower()
                if device_type == 'penta':
                    device_type = 'android'
                if device_type not in ['ios', 'android', 'browser']:
                    device_type = 'etc'
            else:
                device_type = 'etc'

            # Change to use User from issara instead penta
            try:
                user_profile = UserProfile.objects.get(facebook_id=fb_id)
                user = user_profile.user
            except ObjectDoesNotExist:
                user, created = User.objects.get_or_create(
                    username=fb_email.replace('@', '-')
                )
                user_profile, created = UserProfile.objects.get_or_create(user=user)
            except MultipleObjectsReturned:
                # TODO: Handle multiple object return
                raise

            # always update user info
            user.first_name = fb_firstname
            user.last_name = fb_lastname
            user.email = fb_email
            user.save()

            user_profile.first_name = fb_firstname
            user_profile.last_name = fb_lastname
            user_profile.facebook_id = fb_id
            user_profile.image_url = fb_avatarUrl
            user_profile.facebook_access_token = access_token
            user_profile.save()

            if app:
                application_default_role, created = ApplicationDefaultRole.objects.get_or_create(name=app.lower())
            else:
                application_default_role = ApplicationDefaultRole.objects.get_default()
            application_default_role.apply_role_to_user(user)

            device_id = unique_id
            device_type = MobileDevice.Type.get(device_type)
            device_name = '{}-{}'.format(device_type, unique_id)

            device, __ = MobileDevice.objects.get_or_create(user=user, device_id=device_id,
                                                            device_type=device_type)
            device.device_name = device_name
            device.device_token = device_token
            device.is_authorized = True
            device.save()

            token = device.get_token()
            return True, token.key

        except Exception as e:
            logger.exception(str(e))
            return False, 'Failed to create PentaChannel user: %s' % (str(e),)

    def create_guest_user(self, unique_id, time, device_type):
        try:
            prefix = ""
            if device_type.lower() == "android":
                prefix = "ad"
            if device_type.lower() == "ios":
                prefix = "ip"
            if device_type.lower() == "penta":
                prefix = "pt"

            # Seperate guest ID after logout IF USE THIS CODE, USER GUEST WILL RE-CREATE AFTER LOGOUT and RE-LOGIN
            # pUser, userCreated = PentaChannelUser.objects.get_or_create(username=prefix + unique_id + time)

            # USE SAME GUEST ID
            pUser, userCreated = PentaChannelUser.objects.get_or_create(
                    username=prefix + unique_id
                )

            deviceObj, deviceCreated = Device.objects.get_or_create(user=pUser,
                                                                    device_type=device_type,
                                                                    unique_id=unique_id)
            token, tokenCreated = Token.objects.get_or_create(user=pUser)
            return True, token.key
        except:
            return False, str(traceback.format_exc())

    def create_user_and_login(self, login_to_url, email, password, first_name=None, last_name=None):
        result = self.create_user(email, password, first_name, last_name)
        if result[0] is False:
            return result

        login_result = self.post(self.ACTION_GET_CAS_TOKEN, {'email': email, 'service': login_to_url})
        if login_result.status_code == 200:
            return True, login_result.json()['redirect_url']
        return False, 'Failed to auto login'

    def login(self, login_to_url, email, password):
        # check password correct
        r = requests.post('https://accounts.thevcgroup.com/apis/v1/login/',
                          data={'email': email, 'password': password, 'login_url': login_to_url},
                          verify=False)
        if r.status_code == 200:
            # login success
            # generate login ticket
            return True, r.json()['redirect_url']
        elif r.status_code == 403:
            return False, 'Invalid email or password'
        else:
            return False, 'Unknown error'

    def is_user_exists(self, email):
        payload = {'format': 'json',
                   'username': email.replace('@', '-')}
        r = requests.get('%s/user/' % self.API_URL, params=payload, verify=False)
        if r.status_code == 200:
            json = r.json()
            if 'meta' in json:
                if json['meta'].get('total_count', 0) == 1:
                    return True
        return False


if __name__ == '__main__':
    a = AccountAPI()
    # print(a.create_user('test@yoyo.com', 'test'))

    print(a.is_user_exists('natt.ster@gmail.com'))
    success, url = a.create_user_and_login(
        'http://www.pentachannel.com/accounts/login/?next=/th/',
        'natt.ster@gmail.com',
        'test',
        'Firstname',
        'Lastname')
    if success is True:
        print('You should redirect user to ', url)
    else:
        print('Fail to create account, reason = ', url)
