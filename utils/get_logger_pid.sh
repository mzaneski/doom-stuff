#!/bin/bash
ps -e | grep -s -m 1 logger.sh | awk '{print $1}'
