#!/bin/bash
#appends a timestamp to input lines

while read -e line; do
    echo "$(date +%H:%M:%S) $line"
done
