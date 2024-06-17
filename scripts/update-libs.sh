#!/bin/bash

#---- Activating venv
python3 -m venv .venv && source .venv/bin/activate && alias python=.venv/bin/python3 && alias pip=.venv/bin/pip3

#---- Updating the tool libraries
pip install --upgrade pip setuptools wheel
pip install --upgrade pip-chill pip-upgrade-outdated

#---- Listing all the libraries installed
pip-chill -v > requirements-dev.txt

#---- Updating the libraries installed
# pip list --outdated --format=json | jq '.[].name' | xargs -n1 pip install -U
pip_upgrade_outdated

#---- Upgrading pre-commit
pre-commit autoupdate

#---- Separating required libs from deployment libs
required_libs=$(sed 's/==.*//' requirements.txt | tr '\n' '|' | sed 's/|$//')
echo $required_libs
egrep "$required_libs" requirements-dev.txt > requirements.txt
egrep -v "$required_libs" requirements-dev.txt > requirements-dev.txt.bak

#----- Adding the -r requirements.txt line to dev requirements
sed '1s/^/-r requirements.txt\n/' requirements-dev.txt.bak > requirements-dev.txt
rm requirements-dev.txt.bak

#----- The end
echo "Mise à jour des dépendances terminée."