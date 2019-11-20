# Settings

Add to settings.py

```
FACEBOOK_APP_ID = '<Facebook App ID>'
FACEBOOK_APP_SECRET = '<Facebook App secret>'

FACEBOOK_PAGE_ACCESS = [
    {
        'id': '<page_id>',
        'name': '<page_name>*',
        'token': '<Token from APP Messenger Settings>',
    }
]

FACEBOOK_MESSENGER_HOOK_CALLBACK = {
    '<page_name A>': '<handler class A>',
    '<page_name B>': '<handler class B>'
}
FACEBOOK_HOOK_VERIFICATION = '<verification>**'
```

\* You can use `<page name>` whatever you like.
It's just used in this application.
Keep in mind that it has to be unique though.

\** `<verification>` is also can be whatever string you like with some length.
Then you have to set in Facebook webhook with the same string.
Basically, just random it using `pwgen`, `uuid` or whatever.

Add to urls.py

```python
urlpattern = [
    ...
    ('^/messenger/webhook$', django_facebook_messenger.views.webhook_view),
    ...
]
```


## Handler Class

This class view be called from `django_facebook_messenger.views.webhook`
