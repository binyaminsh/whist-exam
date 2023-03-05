#!/bin/bash

docker-compose up -d --scale app=$1
docker-compose exec -T nginx nginx  -s reload
