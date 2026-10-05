#!/bin/bash

docker exec -it orders-pg psql -U ${pguser} -d orders < schema.sql