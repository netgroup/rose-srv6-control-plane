#!/bin/bash

SERVICE=.

DESTDIR='gen-py'
mkdir -p $DESTDIR
python -m grpc_tools.protoc \
    --proto_path=$SERVICE/ \
    --python_out=$DESTDIR \
    --grpc_python_out=$DESTDIR \
    $SERVICE/*.proto

