#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters"
    echo "./script.sh filename"
    exit 1
fi

SED_EXPRESSION="(^\w{3} [ :[:digit:]]{11}) ([._[:alnum:]-]+) ([._[:alnum:]-]*)\[([[:digit:]]+)\]: (.*)"

zcat ${1} | sed -e '1,/=-=-=-/ d' | grep -Ev "^$" | while read line
do
  DATE=$(sed -E "s/${SED_EXPRESSION}/\1/" <<< ${line})
  INDEXDATE=$(date -u -d "$DATE" +"%Y-%m-%d")
  DATE=$(date -u -d "$DATE" +"%Y-%m-%dT%H:%M:%S")
  HOSTNAME=$(sed -E "s/${SED_EXPRESSION}/\2/" <<< ${line})
  SERVICE_NAME=$(sed -E "s/${SED_EXPRESSION}/\3/" <<< ${line})
  PROCESS_ID=$(sed -E "s/${SED_EXPRESSION}/\4/" <<< ${line})
  MESSAGE=$(sed -E "s/${SED_EXPRESSION}/\5/" <<< ${line})

read -r -d '' DATA << EOF
  {
    "@timestamp": "${DATE}",
    "service": "${SERVICE_NAME}",
    "hostname": "${HOSTNAME}",
    "process_id": "${PROCESS_ID}",
    "message": "$(sed 's/"//g' <<< ${MESSAGE})"
  }
EOF

  curl --header "Content-Type: application/json" \
  --request POST \
  --data "${DATA}" \
  -u 'login:password' \
  https://es-server:9200/logcheck-${INDEXDATE}/_doc/ &
done

rm ${1}

