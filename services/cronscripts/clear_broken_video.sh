#!/bin/bash

cd ${0%/*}/..
source ../env/bin/activate

python manage.py clear_broken_video  --settings=showtime.settings_monitor
