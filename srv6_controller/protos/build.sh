#!/bin/bash

SERVICE=.

DESTDIR='gen-py'
mkdir -p $DESTDIR
source /home/rose/.rose-venv/bin/activate
python3 -m grpc_tools.protoc \
    --proto_path=$SERVICE/ \
    --python_out=$DESTDIR \
    --grpc_python_out=$DESTDIR \
    $SERVICE/*.proto

