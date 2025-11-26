#!/bin/bash

usage() {
    echo "Usage: $0 <container> <topic> [-c] [-l] [-r]"
    echo "  -c  Create topic"
    echo "  -l  List/describe topic"
    echo "  -r  Remove/delete topic"
    exit 1
}

if [ $# -lt 3 ]; then
    usage
fi

CONTAINER=$1
TOPIC=$2
shift 2

CREATE=0
LIST=0
REMOVE=0

while getopts "clr" opt; do
    case $opt in
        c) CREATE=1 ;;
        l) LIST=1 ;;
        r) REMOVE=1 ;;
        *) usage ;;
    esac
done

if [ $CREATE -eq 1 ] && [ $REMOVE -eq 1 ]; then
    echo "Error: -c and -r cannot be used together"
    exit 1
fi

if [ $CREATE -eq 0 ] && [ $LIST -eq 0 ] && [ $REMOVE -eq 0 ]; then
    echo "Error: At least one of -c, -l, or -r must be specified"
    exit 1
fi

if [ $CREATE -eq 1 ]; then
    echo "Creating topic: $TOPIC"
    docker exec -it $CONTAINER /opt/kafka/bin/kafka-topics.sh --create --topic $TOPIC --bootstrap-server localhost:9092
fi

if [ $LIST -eq 1 ]; then
    if [ $CREATE -eq 1 ]; then
        echo ""
        echo "Describing topic: $TOPIC"
    else
        echo "Describing topic: $TOPIC"
    fi
    docker exec -it $CONTAINER /opt/kafka/bin/kafka-topics.sh --describe --topic $TOPIC --bootstrap-server localhost:9092
fi

if [ $REMOVE -eq 1 ]; then
    if [ $LIST -eq 1 ]; then
        echo ""
        echo "Removing topic: $TOPIC"
    else
        echo "Removing topic: $TOPIC"
    fi
    docker exec -it $CONTAINER /opt/kafka/bin/kafka-topics.sh --delete --topic $TOPIC --bootstrap-server localhost:9092
fi
