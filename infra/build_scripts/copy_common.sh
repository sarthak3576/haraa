#!/usr/bin/env bash
# Copies the minimal shared app/ subset every /api/v1/* function needs
# (config + the boto3-client factories + the shared category data) into
# $1/app/. Each function's Makefile target then copies its own extra
# service files and handler.py on top of this.
set -euo pipefail
DEST="$1"

# app/config.py unconditionally does `from dotenv import dotenv_values`.
# These lightweight functions intentionally carry no pip layer (see
# Makefile), but python-dotenv is pure Python (universal wheel) so it's
# cheap to vendor directly rather than pull in the whole WebDepsLayer.
/usr/bin/python3 -m pip install python-dotenv --no-deps --target "$DEST" --quiet

mkdir -p "$DEST/app/services"
cp app/__init__.py "$DEST/app/"
cp app/config.py "$DEST/app/"
cp app/aws_clients.py "$DEST/app/"
cp app/env_file_io.py "$DEST/app/"
cp app/services/__init__.py "$DEST/app/services/"
cp app/services/waste_categories.py "$DEST/app/services/"
