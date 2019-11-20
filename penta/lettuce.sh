#!/bin/bash


case $1 in
    "install" )
        echo "install"
        # test depdendencies
        pip install -q lettuce git+https://github.com/bbangert/lettuce_webdriver.git nose ipdb
        pip uninstall -q -y unittest2
        if [ -z "${GDMSESSION}" ]; then
             # for non X environment
             pip install -q pyvirtualdisplay
        fi
    ;;
    * )
        python manage.py makemessage --settings=showtime.lettuce_settings -l th
        python manage.py compilemessages --settings=showtime.lettuce_settings
        python manage.py harvest --settings=showtime.lettuce_settings -a feed $*
    ;;

esac
