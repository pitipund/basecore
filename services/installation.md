Penta Center Installation
=========================
*Updated April 26th, 2018*

This is how to install Full version Penta Center
without Docker.

List of components on Penta Center server that should be included.

- Penta Channel or Showtime (This project) [link](http://192.168.10.21/pentatv/showtime)
- Penta Search [link](http://192.168.10.21/pentatv/penta-search)
- Penta Wallet [link](http://192.168.10.21/pentatv/penta-wallet)

Index
-----

- [Install Penta Channel](#install-penta-channel)
  - [Install Dependencies](#dependencies)
  - [Install Submodules](#install-submodules)

Install Penta Channel
---------------------

### Dependencies

```
sudo apt update && sudo apt upgrade -y
sudo apt install python2.7 python-pip
sudo apt install libmysqlclient-dev libsasl2-dev \
                 libssl-dev libffi-dev libpython-dev

pip install virtualenv
```

Create virtual env

```
cd <project-directory>
virtualenv env -p python2.7
```

Activate virtualenv
```
. env/bin/activate
```

Install python dependency
```
pip install -r requirements.txt
pip install uwsgi
```

Add user to `adm` and `www-data` groups
```
usermod -aG adm <admin-user>
usermod -aG www-data <admin-user>
```


### Install submodules

```
git submodule init
git submodule sync
git submodule update
```

if you cannot clone submodules using git,
you can copy submodule code to production directly.

```
scp -r <django_wallet_client> \
    <admin>@<production>:<project-directory>/django_wallet_client
scp -r <django_facebook_messenger> \
    <admin>@<production>:<project-directory>/django_facebook_messenger
```


Install Database
----------------

Newly approach is using Percona Xtra Cluster on Kubernetes.
But, in case, you're not using them. You can install MySQL.

```
sudo apt install mysql
```

Then run mysql secure to initial security settings.

```
mysql_secure_installation
```

To create database, login to mysql client and use this command (also in Percona).

```
CREATE DATABASE showtime CHARACTER SET utf8mb4
       COLLATE utf8mb4_unicode_ci;
```
*It has to be **utf8mb4**, seriously!, or some functions will be broken*

For create user
```
GRANT ALL PRIVILEGES ON showtime.*
    TO 'showtimedc'@'localhost'
    IDENTIFIED BY '<randomly generated long password>';
FLUSH PRIVILEGES;
```


Create directory
----------------
```
mkdir -p -m775 /var/log/uwsgi /var/log/pentachannel \
        /var/log/pentachannel_persistent /var/uwsgi
chown -R www-data:adm /var/log/uwsgi /var/log/pentachannel \
        /var/log/pentachannel_persistent
chown -R www-data:www-data /var/uwsgi
```


Install Web Server
------------------

Strongly recommend `nginx` and strongly reject `apache`

```
sudo apt install nginx
```

After **configure Nginx** you also need to install `certbot`.
[here](https://certbot.eff.org/docs/install.html)


Install Cache
-------------

We use `redis` for cache server

```
sudo apt install redis-server
```


Install Uwsgi
-------------
Use `which` to see path of uwsgi
(if you cannot found, maybe, you didn't activate the virtualenv yet)

```
$ which uwsgi
> <path-to-uwsgi>/uwsgi
```

Then create systemd configure

/etc/systemd/system/uwsgi.service
```
[Unit]
Description=uWSGI Emperor
After=syslog.target

[Service]
ExecStart=<path-to-uwsgi>/uwsgi --emperor /etc/uwsgi/vassals/ --pidfile /var/uwsgi/uwsgi.pid
ExecReload=/bin/kill -HUP $MAINPID
RuntimeDirectory=uwsgi
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```


Settings
--------

### Nginx
/etc/nginx/conf.d/penta.center.conf
```
upstream pentachannel {
    server unix:///var/uwsgi/pentacenter.sock;
}

# uncomment to redirect all https (may break PentaBox)
#server {
#    listen 80 default_server;
#    return 301 https://$host$request_uri;
#}
server {
    listen 80;
    listen 443 ssl http2 default_server;
    server_name www.penta.center penta.center;
    #ssl on;
    ssl_certificate /etc/letsencrypt/live/penta.center/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/penta.center/privkey.pem;

    # location /media {
    #     alias /home/showtime/beta_showtime/media;
    #     expires 168h;
    #     add_header Pragma public;
    #     add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    # }
    location /media/uploaded/wallpaper/current.jpg {
        try_files $uri @proxy_to_app;
    }
    location /media/uploaded/wallpaper/h3_current.jpg {
        try_files $uri @proxy_to_app;
    }
    location /media/uploaded/wallpaper/h3_inter_current.jpg {
        try_files $uri @proxy_to_app;
    }
    location ~ ^/media/airtech/(?<path>.*) {
        alias /home/showtime/beta_showtime/media/airtech/$path;
        expires 168h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    location ~ ^/media/sqool/(?<path_sq>.*) {
        alias /home/showtime/beta_showtime/media/sqool/$path_sq;
        expires 168h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    location =/media/random2000x2000.png {
        alias /home/showtime/beta_showtime/media/random2000x2000.png;
        expires 168h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    location /staticcontent {
        alias /home/showtime/staticcontent;
        auth_basic "Restricted";
        auth_basic_user_file /home/showtime/staticcontent/.htpasswd;
    }
    location /static {
        alias /home/showtime/beta_showtime/production_static;
        expires 24h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }

    # For penta search
    location /penta_search {
        alias /home/showtime/penta_search;
    }

    location / {
        try_files $uri @proxy_to_app;
        proxy_connect_timeout 300;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
        send_timeout 300;
        client_max_body_size 1024M; # Set higher depending on your needs
    }

    location @proxy_to_app {
        uwsgi_pass pentachannel;
        include uwsgi_params;
        proxy_set_header  X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

```


### Uwsgi
/etc/uwsgi/vassals/pentacenter.ini
```
[uwsgi]
master = true
processes = 20
# threads = 2
socket = /var/uwsgi/pentacenter.sock
chmod-socket = 664
enable-threads = true
single-interpreter = true
thunder-lock = true
listen = 1024
module = showtime.wsgi
pythonpath = /home/showtime/beta_showtime/
logto = /var/log/uwsgi/pentacenter-wsgi.log
logfile-chown = www-data  # You may not need this, based on your setup
env = DJANGO_SETTINGS_MODULE=showtime.production
chdir = /home/showtime/beta_showtime/
smart-attach-daemon = /var/uwsgi/celery.pid DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/celery -A showtime worker --time-limit=300 -l info -f /var/log/uwsgi/celery.log --pidfile=/var/uwsgi/celery.pid
harakiri = 120
uid = www-data
gid = www-data
touch-logreopen = /var/log/uwsgi/logrotate.trigger
home = /home/showtime/env/
stats = /var/uwsgi/showtime_stat
vacuum = true
disable-logging = true
```

### Logrotate

/etc/logrotate.d/pentacenter
```
/var/log/pentachannel/access.log
/var/log/pentachannel/access_report.json
/var/log/pentachannel/user_report.json {
  copytruncate
  daily
  rotate 10
  compress
  missingok
  notifempty
}

/var/log/pentachannel_persistent/*.log {
  weekly
  copytruncate
  compress
  dateext
  missingok
  sharedscripts
  postrotate
    touch /var/log/uwsgi/logrotate.trigger
  endscript
}
```

/etc/logrotate.d/uwsgi
```
/var/log/uwsgi/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0660 www-data adm
    sharedscripts
    postrotate
        touch /var/log/uwsgi/logrotate.trigger
    endscript
}
```


### Penta Center Settings

```
cd <project-root>/showtime
cp production_example.py production.py
cp settings_monitor_example.py settings_monitor.py
```


### CronTab settings

Enter crontab
```
crontab -e
```

Paste (don't forget to replace path first)
```
# m h  dom mon dow   command

# customer related crons
1 5 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py update_wallpaper

30 2 * * * bash /home/showtime/beta_showtime/clear_template_snapshot.sh

# clear django session at midnight everyday
0 0 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py clearsessions

# generate daily access report
0 2 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py generate_daily_report

# send live channel error report
0 */3 * * * DJANGO_SETTINGS_MODULE=showtime.settings_monitor /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py report_bad_channel > /tmp/report_bad_channel.log

# clear PentaTV and PentaSearch garbage links
0 0 * * 3 DJANGO_SETTINGS_MODULE=showtime.settings_monitor /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py clear_broken_video
0 23 * * 0,1,2,4,5,6 DJANGO_SETTINGS_MODULE=showtime.settings_monitor /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py clear_broken_video --day_back 30
50 23 * * 0 DJANGO_SETTINGS_MODULE=showtime.settings_monitor /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py clear_broken_video --send_summary 7

# update highlight videos
0 */4 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py get_highlight

# update highlight videos for weekly
# 8 19 * * 5 /home/showtime/beta_showtime/env/bin/python /home/showtime/beta_showtime/manage.py get_highlight 0 7
# 8 20 * * 6 /home/showtime/beta_showtime/env/bin/python /home/showtime/beta_showtime/manage.py get_highlight 0 7

# send email about update videos to followers every Tuesday, Thursday, Friday and Saterday night
# have to separate due to gmail limit
# 10 17 * * 2,4 /home/showtime/beta_showtime/env/bin/python /home/showtime/beta_showtime/email_every_day.py
# 10 18 * * 5 /home/showtime/beta_showtime/env/bin/python /home/showtime/beta_showtime/email_every_day.py
# 10 19 * * 6 /home/showtime/beta_showtime/env/bin/python /home/showtime/beta_showtime/email_every_day.py

# log amount of subscriber
0 23 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/log_subscriber.py

# update video from auto system
30 */4 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/update_auto_video.py

# update view stat from rocklog
30 4 * * * DJANGO_SETTINGS_MODULE=showtime.production /home/showtime/env/bin/python /home/showtime/beta_showtime/manage.py summary_channel_view 1 7

# update youtube-dl daily
0 0 * * * /home/showtime/env/bin/python -m pip install youtube-dl --upgrade
```

### Settings bash shell

add these lines to `<admin-home>/.bashrc`
```
...

# at the end of file
export DJANGO_SETTINGS_MODULE=showtime.production
. ~/env/bin/activate
```


Starting/Restart Services
-------------------------

start all services
```
sudo systemctl start nginx uwsgi redis-server [mysql]
```

restart all services
```
sudo systemctl restart nginx uwsgi redis-server [mysql]
```

Troubleshooting
---------------

- Error log at `/var/log/uwsgi/pentachannel_error.log`
- Using `uwsgitop`

  ```
  # install uwsgitop
  pip install uwgitop

  # use uwsgitop
  uwsgitop /var/uwsgi/showtime_stat
  ```

