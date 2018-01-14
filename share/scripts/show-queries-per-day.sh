#!/bin/bash

# show how many HTTP queries 
# rate.sx processes each day

sudo cat /var/log/nginx/rate.sx-access.log | awk '{print $4}' | sed 's/:.*//; s/^.//' | uniq -c

