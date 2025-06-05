#!/bin/bash

rq worker -c distproc.redis_conf --with-scheduler low
