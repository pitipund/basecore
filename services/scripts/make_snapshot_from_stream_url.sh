#!/bin/bash

HEIGHT_SCALE=720
TARGET_DIR=/home/showtime/beta_showtime/media/snapshot

function print_usage {
cat <<EOF
Usage: $0 youtube_video_url
EOF
}

YOUTUBE_URL=$1
#VIDEO_ID=$(echo $YOUTUBE_URL | cut -d '?' -f2 | cut -d '&' -f1 | cut -d '=' -f2)

VIDEO_ID=${2:-$(echo -n $YOUTUBE_URL | md5sum | cut -d' ' -f1)}

STREAM_URL=$YOUTUBE_URL
if [ $? -ne 0 ] ; then
  print_usage
  exit -1
fi

DURATION=$(ffmpeg -i $STREAM_URL 2>&1 | grep Duration | cut -d, -f1 | cut -d. -f1 | awk '{print $2}')
DELIMITER=${DURATION//[^:]}
DELIMIT_NUM=${#DELIMITER}

case $DELIMIT_NUM in
  0)
    TIME=$DURATION
    INTERVAL=$(((TIME/11)))
    ;;
  1)
    MIN=$(echo $DURATION | cut -d: -f1)
    SEC=$(echo $DURATION | cut -d: -f2 | sed 's/^0*//')
    TIME=$(((MIN*60 + SEC)))
    INTERVAL=$(((TIME/11)))
    ;;
  2)
    HOUR=$(echo $DURATION | cut -d: -f1)
    MIN=$(echo $DURATION | cut -d: -f2 | sed 's/^0*//')
    SEC=$(echo $DURATION | cut -d: -f3 | sed 's/^0*//')
    TIME=$(((HOUR*3600 + MIN*60 + SEC)))
    INTERVAL=$(((TIME/11)))
    ;;
  *)
    echo "read time error (delimiter=${DELIMITER}_${DELIMIT_NUM})"
    exit 1
esac

cat <<EOF
Youtube URL: $YOUTUBE_URL
Video ID:    $VIDEO_ID

Stream URL:  $STREAM_URL

Duration: $DURATION
Time: ${TIME}s
Interval: ${INTERVAL}s
EOF
# Delimiter: $DELIMITER $DELIMIT_NUM
# echo -n Press any key to continue
# read -n 1 dump

if [ x$TARGET_DIR == x ] ;then
  DIR=$VIDEO_ID
else
  DIR=$TARGET_DIR/$VIDEO_ID
fi

#[ -e $VIDEO_ID ] && echo "clean old files" && rm -r $VIDEO_ID
[ -e $DIR ] && echo "Folder existed" && exit 0
mkdir $DIR

echo
echo "Images will be created in folder ${VIDEO_ID}/"
for n in $(seq 10); do
  ffmpeg -ss $(((INTERVAL*$n))) -i $STREAM_URL -vf scale=-1:$HEIGHT_SCALE -frames:v 1 -an -loglevel 0 $DIR/$(printf %02d $n).jpg
  echo -n .
done
echo
exit 0

