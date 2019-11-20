#!/usr/bin/python
# cron for email, check link dead, backup showtime database.
SCRIPTPATH='$0'
DIR="$( cd -P "$( dirname "$SCRIPTPATH" )" && pwd )"
crontab -l > cron_every_day
#     m h dom mon dow
echo "0 17 * * *" /usr/bin/python $DIR/email_every_day.py >> cron_every_day #/home/showtime/beta_showtime/env/bin/python
echo "0 1 * * *" /usr/bin/python $DIR/check_link_dead.py >> cron_every_day
echo "0 3 * * *" bash $DIR/backup_showtime_db.sh >> cron_every_day

crontab cron_every_day