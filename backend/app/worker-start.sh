#! /usr/bin/env bash
set -e

hatch run python /app/app/worker_pre_start.py
hatch run celery -A app.worker worker -l info -Q main-queue -c 1
