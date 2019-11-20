#!/bin/bash

cd ${0%/*}/..
source ../env/bin/activate

python manage.py clear_broken_video --send_summary 7 --settings=showtime.settings_monitor
