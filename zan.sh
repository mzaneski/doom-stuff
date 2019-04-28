#!/bin/bash

#This script is used for running a SINGLE Zandronum server.

#----------------
#HOSTNAME_VAR - Set this to always override the ENTIRE automatic hostname.
#               You can also use the -n flag to do this from the command line.
HOSTNAME_VAR=""

#CLANTAG_VAR - This string appears at the beginning of the automatic hostname.
#NOTE_VAR - This string will show at the end of the automatic hostname.
CLANTAG_VAR="DOOM"
NOTE_VAR=""

DEFAULT_IWAD="doom2.wad"

#*_DIR - Search directories for WADs and config files. These need a / at the end.
IWAD_DIR="./IWAD/"
PWAD_DIR="./PWAD/"
CONFIG_DIR="./config/"

#*_CFG - Default config names for the main server, hostname, and map rotation configs.
SERVER_CFG="server.cfg"
HOSTNAME_CFG="hostname.cfg"
ROTATION_CFG="rotation.cfg"
#----------------

#option variables
hname=$HOSTNAME_VAR
iwad=$DEFAULT_IWAD
conf=""
declare -i max=6
declare -i allow_multiple=0
declare -i killserver=0
declare -i restart_server=0

#param variables
pwads=""

#script variables
hostname_cfg=""
pwad_names=""
conf_name=""
server=""
pid=""
declare -i num_servers=0

#strings
INFO_KILL="Zandronum server killed."
ERR_UNKNOWN="Unknown option. Use -h for help."
ERR_RUNNING="Zandronum is already running. Use -k/-r to kill/restart it or -m to allow creating multiple instances."
ERR_KILL="You used option -k/-r (kill/restart) but there is no Zandronum server running."
ERR_KILL2="You used option -k/-r (kill/restart) but there are multiple servers running."

while [ -n "$1" ]; do
    case "$1" in
        -h) echo "Usage: ./zan.sh [options] -- [params]"
        echo "Options:"
        echo "  -h        : prints this help"
        echo "  -k        : kill the server (and abort this script)"
        echo "  -r        : restart the server"
        echo "  -m        : allow multiple instances"
        echo ""
        echo "  -i [filename] : set iwad (Default: doom2.wad)"
        echo "  -c [filepath] : optional config file to execute after server.cfg"
        echo "  -n [str]  : disable automatic hostname and override it with a string"
        echo "  -p [int]  : set max players (Default: 6)"
        echo ""
        echo "Params:"
        echo "  *.wad *.pk3"
        exit 0 ;;
        -k) killserver=1 ; break ;;
        -r) killserver=1 ; restart_server=1 ;;
        -m) allow_multiple=1 ;;
    	-i) iwad="$2" ; shift ;;
        -c) conf="$2" ; shift ;;
        -n) hname="$2" ; shift ;;
        -p) max=$2 ; shift ;;
        --) shift ; break ;;
        *)  echo "$1 : $ERR_UNKNOWN" ; exit 1 ;;
    esac
    shift
done

server=$(ps -e | grep -s zandronum-serv)

if [ -z "$server" ]; then
    num_servers=0
else
    num_servers=$(echo $server | wc -l)
fi

if [ $killserver -eq 1 ]; then
    if [ $num_servers -eq 1 ]; then
        pid=$(echo $server | awk '{print $1}')
        kill $pid
        num_servers=$num_servers-1
        echo $INFO_KILL
        if [ ! $restart_server -eq 1 ]; then
            exit 0
        fi
    elif [ $num_servers -lt 1 ]; then
        echo $ERR_KILL
        exit 1
    else
        echo $ERR_KILL2
        exit 1
    fi
fi

if [ $num_servers -gt 0 ]; then
    if [ ! $allow_multiple -eq 1 ]; then
        echo $ERR_RUNNING
        exit 1
    fi
fi

while [ -n "$1" ]; do
    pwad_names="$pwad_names $1"
    pwads="$pwads $PWAD_DIR$1"
    shift
done

if [ ! -z "$conf" ]; then
    conf_name=${conf##*/}
    conf_name=${conf_name%%.*}
fi

if [ -z "$hname" ]; then
    hostname_cfg="$CONFIG_DIR$HOSTNAME_CFG"
    touch $hostname_cfg
    echo "sv_hostname \"$CLANTAG_VAR | $conf_name | $(echo $pwad_names | tr ' ' '\n' | grep -s -m 1 ".wad$")$NOTE_VAR\"" > $hostname_cfg
fi

echo "Starting server for $max players..."
if [ -z "$hname" ]; then
    echo "host:  $(cut -f 2- -d ' ' $hostname_cfg)"
else
    echo "host:  $hname"
fi
echo "iwad:  $iwad"
echo "pwad:  $pwad_names"
echo "mode:  $conf_name"

zandronum-server -iwad "$IWAD_DIR$iwad" +sv_hostname "$hname" -host $max -file $pwads +exec "$CONFIG_DIR$SERVER_CFG" $conf $hostname_cfg "$CONFIG_DIR$ROTATION_CFG" -noinput -nobroadcast 2>&1 | ./utils/logger.sh > logs &
