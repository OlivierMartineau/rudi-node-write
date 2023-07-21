#!/bin/bash

pip list --outdated --format=json | jq '.[].name' | xargs -n1 pip install -U
pre-commit autoupdate
