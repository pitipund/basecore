#!/bin/bash

cd ${0%/*}/..
source ../env/bin/activate

python manage.py clean_expire_soop_video  --settings=showtime.settings_monitor
python manage.py clear_dead_soop_video  --settings=showtime.settings_monitor
