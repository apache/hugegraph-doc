#!/bin/bash

INSTALL_DIR=${INSTALL_DIR}
REPO=${REPO}
REPO_URL=${REPO_URL}

# wait_for_startup friendly_name url timeout_s
function wait_for_startup() {
    local server_name="$1"
    local server_url="$2"
    local timeout_s="$3"

    local now_s=`date '+%s'`
    local stop_s=$(( $now_s + $timeout_s ))

    local status

    echo -n "Connecting to $server_name ($server_url)"
    while [ $now_s -le $stop_s ]; do
        echo -n .
        status=`curl -o /dev/null -s -w %{http_code} $server_url`
        if [ $status -eq 200 ]; then
            echo "OK"
            return 0
        fi
        sleep 2
        now_s=`date '+%s'`
    done

    echo "The operation timed out when attempting to connect to $server_url" >&2
    return 1
}

PID=`ps aux | grep "$REPO" | grep -v 'grep' | awk '{print $2}'`

if [ -n "$PID" ]; then
    kill -9 $PID
fi

rm -rf $INSTALL_DIR/$REPO

git clone $REPO_URL/$REPO $INSTALL_DIR/$REPO || exit 1

# Jenkins will kill process with current BUILD_ID
# http://wiki.jenkins-ci.org/display/JENKINS/Spawning+processes+from+build
# http://excid3.com/blog/running-background-daemon-scripts-with-jenkins
OLD_BUILD_ID=$BUILD_ID
BUILD_ID=dontKillMe
gitbook serve --port 8001 $INSTALL_DIR/$REPO &
BUILD_ID=$OLD_BUILD_ID

wait_for_startup $REPO http://localhost:8001 30

if [ $? -eq 0 ]; then
    echo "Deploy OK!"
    exit 0
else
    echo "Deploy Failed!"
    exit 1
fi
