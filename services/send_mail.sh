#!/usr/bin/python
SCRIPTPATH='$0'
DIR="$( cd -P "$( dirname "$SCRIPTPATH" )" && pwd )"
crontab -l > send_mail
echo "0 17 * * 5" /usr/bin/python $DIR/send_mail.py >> send_mail
#     m h dom mon dow
crontab send_mail