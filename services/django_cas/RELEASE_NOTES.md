Release Notes
-------------

## Version KTH-2.0.3

* Fix broken packaging in 2.0.2 causing management command to be missing.

## Version KTH-2.0.2

* Don't store session service tickets when single sign out is disabled.
* Fix, or rather work around for issue with session - service ticket mappings
  being left in the database in some cases, making the table grow indefinitely.
    
  The solution is to add a post_delete handler which should remove session
  service ticket objects when the session is deleted from the database, when
  the management command `cleanup` is run if nothing else.

  If the session is not mapped to the database this is not enough however, in
  which case you'd have to run the new `purge_session_service_tickets` management
  command periodically.

## Version KTH-2.0.1

* Fix a KeyError being thrown when checking if the session was authenticated
  by cas on sign out.

## Version KTH-2.0.0

This major release targets Django 1.4 and later. That said, most of it will
work fine in earlier versions, but it is recommended to stay with 1.2.0 if 
you use older versions of Django.

* Support for CAS gateway request by setting CAS_GATEWAY, see [README](README.md)
  for more information.
* Improved API for proxy granting tickets
  * ```get_tgt_for()``` is now ```Tgt.get_tgt_for_user()``` and can take
    a User object or username as argument.
  * ```Tgt.get_proxy_ticket_for()``` is now ```Tgt.get_proxy_ticket_for_service()```.
  see [PROXY_AUTHENTICATION](PROXY_AUTHENTICATION.md) for more information.
* Raise PermissionDenied instead of returning inline HttpResponseForbidden 
  and let Django framework deal with responding properly. Django 1.4 has a 
  new 403 handler to customize behaviour.
* Dropped django_cas.decorators. This refactorization enters Django 1.4 land.
  The funcionality of django_cas.decorators is available in the standard
  permission_required decorator in Django 1.4, using the option raise_exception.
  
  E.g:
  ```
  from django.contrib.auth.decorators import permission_required
  
  @permission_required('some.permission', raise_exception=True)
  def view_function():
      ...
  ```
  If you need this decorator, upgrade to Django 1.4 if you haven't already. 
  If you need this decorator and have to stay on Django 1.3, stay with version 1.2.0
  of this module.

## Version KTH-1.2.0

* Dropped 'next_page' and 'required' parameters from views.login and
  'next_page' from views.logout. I did not see a proper use case for these
  parameters and will regard these as undocumented private features,
  hence only a minor version number bump.
* Fix possible UnicodeEncodeErrors in GET parameters. The only actual
  case I've seen of actually using the parameters mentioned above.

## Version KTH-1.1.0

* Add CAS_RENEW setting to enforce CAS renew feature. See [README](./README.md)
  regarding this setting and CAS_LOGOUT_COMPLETELY.
* Dropped the CAS_LOGOUT_REQUEST_ALLOWED setting. It implicated in my view 
  security it didn't really provide. See [README](./README.md) for more information.

## Version KTH-1.0
 
* Completed fork of project.

## Version 2.0.3-KTH-11

* Incorporated support for single sign out. 
* Project has since then moved to other repository and all pull requests 
  seem to be thrown away, so the project seems officially a dead end 
  for other purposes than the ones intended by the maintainer.
* Heavily refactorized.
  * Removed support for CAS 1.0.
  * Removed support for old Python versions.
  * Removed lots of other dead code.
  * Improved XML handling.
  * Added logging.
  * Lots of clean ups.
* Add setting CAS_SINGLE_SIGN_OUT True/False to allow for turning 
  off single sign out support, default True.
* Add setting CAS_ALLOWED_PROXIES [list of URLS] to support basic 
  filtering of allowed proxy servers, not tested.
* Add setting CAS_AUTO_CREATE_USERS True/False to control behavior
  where backend auto creates users that are logged in, default False.

## Version 2.0.3-KTH-10
 
* Added support for CAS proxy authentication.
* Removed messaging.
