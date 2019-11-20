#!/bin/bash
DATE=$(date +'%Y%b%d')
USERNAME='root'
PASSWORD='powerall'
DB='showtime'
mysqldump -u$USERNAME -p$PASSWORD $DB | gzip > $DB$DATE.sql.gz
mv $DB$DATE.sql.gz /home/showtime/backups/