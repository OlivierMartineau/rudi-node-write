#!/bin/bash

pip list --outdated --format=json | jq '.[].name' | xargs -n1 pip install -U
pip install --force-reinstall -v "questionary==1.4.0"
pre-commit autoupdate
