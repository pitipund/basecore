#!/bin/bash
# Linux
#sudo apt-get -y install python-pip
# OSX
#sudo easy_install pip
#sudo pip install virtualenv

if [ ! -z $1 ] 
then 
    NAME=$1
else
    NAME=env
fi

if [ -d $NAME ]; then
    echo "> virtualenv exists"
else
    echo "> creating virtualenv $NAME"
    virtualenv $NAME
fi

source $NAME/bin/activate

export PIP_DOWNLOAD_CACHE=$HOME/.pip_download_cache
pip install -r requirements.txt --user
