#!/bin/bash
SRC="/vanmanga/frontend/static/js/config.js"

if [ -z $SRC ] || [ ! -e "$SRC" ]; then
    echo "Source file '$SRC' does not exist"
    exit 1
fi

OUTPUT="// generated"

while IFS="" read -r line || [ -n "$line" ]; do
    use_line=$line

    if [[ $line =~ "window." ]]; then
        ENVIRONMENT_VARIABLE_NAME=`echo $line | sed -re 's/window\.(.*)\s+\=(.*);/\1/g'`
        ENVIRONMENT_VARIABLE_NAME="${ENVIRONMENT_VARIABLE_NAME/$'\r'/}"
        value=${!ENVIRONMENT_VARIABLE_NAME}
        if [[ ${value} && ${value-x} ]]; then
            use_line="window.$ENVIRONMENT_VARIABLE_NAME = '$value';"
            echo "$use_line"
        fi
    fi

    OUTPUT="$OUTPUT\n$use_line"
done <$SRC

echo -en $"$OUTPUT" > "$SRC"
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5000 main:app
