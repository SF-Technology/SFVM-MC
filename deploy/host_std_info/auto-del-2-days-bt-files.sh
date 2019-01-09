#!/bin/sh
find /app/clone|grep task -mtime +2 -exec rm -rf {} \;