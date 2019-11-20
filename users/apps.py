from collections import OrderedDict

from django.apps import AppConfig
from django.conf import settings
from constance.signals import config_updated
from django.dispatch import receiver

DEFAULT_SESSION_TIMEOUT = 7 * 24 * 60


class UsersConfig(AppConfig):
    name = 'his.users'
    verbose_name = "Users"

    config = OrderedDict([
        ('DEFAULT_APPLICATION_NAME', ('', 'Default application name of ApplicationDefaultRole for assign roles '
                                          'to a new user that doesn\'t specific a application name.'
                                          'If not set, the first created ApplicationDefaultRole will be used', str)),
        ('MAXIMUM_SESSION_PER_USER', (0, 'Maximum number of simultaneous sessions allowed for single user\n'
                                         '0 = unlimited', int)),
        ('INACTIVITY_TIMEOUT', (500, '(minutes) System will lock screen, and prompt user to relogin\n'
                                     'when this timeout expired')),
        ('SESSION_TIMEOUT', (DEFAULT_SESSION_TIMEOUT, '(minutes) System will force user to relogin\n'
                                                      'when timeout expire (default to 7 days)')),
        ('PASSWORD_AGE', (0, '(day) Password expire every x day (0 = password never expire)', int)),
        ('PASSWORD_MIN_LENGTH', (8, '(characters) Minimum password length', int)),
        ('PASSWORD_HISTORY', (3, 'User cannot reuse password from x password history. (0 = disable this check)', int)),
        ('LDAP_ENABLED', (False, 'Enable authentication against LDAP Server', bool)),
        ('LDAP_SSL', (False, 'LDAPS (LDAP over SSL)', bool)),
        ('LDAP_HOST', ('', 'Host name or IP Address of LDAP Server', str)),
        ('LDAP_PORT', (389, 'LDAP Server port', int)),
        ('LDAP_DOMAIN', ('ad.thevcgroup.com', 'Full domain of LDAP Server', str)),
        ('LDAP_TIMEOUT', (5, '(second) LDAP Connection / Receive timeout', int)),
        ('LDAP_FIRST_NAME_ATTR', ('givenName', 'LDAP Attribute to retrieve first name', str)),
        ('LDAP_LAST_NAME_ATTR', ('sn', 'LDAP Attribute to retrieve last name', str)),
        ('EMPLOYEE_CODE_LENGTH', (8, 'Length of employee code (used for zero-padding Username)', int)),
        ('TECHNICIAN_CODE', ('T', 'position techician code', str)),

        ('MAX_EXPERIENCE_FOR_LEVEL1', (2, 'Level1 คือ อายุงานไม่เกิน x ปี', int)),
        ('MAX_EXPERIENCE_FOR_LEVEL2', (4, 'Level2 คือ อายุงานไม่เกิน x ปี', int)),

        ('OTP_TIMEOUT', (5, "OTP timeout in minutes", int)),
        ('FCM_API_KEY_PENGUIN',
         ("AAAAjxtg2BM:APA91bEWFOARNIZeZEJqsCSyR7jLs8vwcAu2VMCqPsw1nZmmQr6fDJxZS0VIGu6eEm-ct2tqR0lfR9WiKuq"
          "bkEprOdWVuAOb7GXEk6oKX-n3y25xGad87fGYm0fAgBUtVvPbboQgWjfS",
          "firebase api key penguin", str)),
        ('FCM_API_KEY_SLOT',
         ("AAAAEXUwoDQ:APA91bGy9IQQnt-ghULq1lb0-ThnAzjsgEAtRbcseXwDQXCDJYzLkvWI_a7MGEynEQhZJslKWDyvjD6__SIV"
          "5Vs75a7OajdPzAog9YuSb5GsKyOnr3J35VJY-Cxs5STD5OaxwONUSuyk", "firebase api key slot", str)),
        ('FCM_SERVER_KEY_ISNURSE',
         ('AAAAfwdI4Qk:APA91bHCKl7LnJIguWKSCpD7aNoG99H-FuwQN7Gn6nutohBiwsfZR2gkF3zkRxen6sUDsSH'
          'LAut3xMnQJ2R_WBRl65GytC1AJa_SH-jJGqPdwjjmPV93OMA6a0JCEQfDp57RWsEsJ42H', 'firebase api key isnurse', str))
    ])

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        UsersConfig.setup_session_settings(DEFAULT_SESSION_TIMEOUT)

    @classmethod
    def setup_session_settings(cls, session_timeout):
        settings.SESSION_COOKIE_AGE = session_timeout * 60  # convert minute to second


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    # TODO(natt): this signal handler won't get called in multi-server deployment
    # we need to use other mechanism to notify of DJANGO settings changed
    if key == 'users_SESSION_TIMEOUT':
        UsersConfig.setup_session_settings(new_value)
