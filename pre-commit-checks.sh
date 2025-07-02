#!/bin/bash

echo "----- Activating venv"
VENV_DIR=.venv &&
    python3.12 -m venv $VENV_DIR &&
    source $VENV_DIR/bin/activate &&
    alias python=$VENV_DIR/bin/python3 &&
    alias pip=$VENV_DIR/bin/pip3

echo "----- Updating the tool libraries"
pip install --upgrade pip setuptools wheel
pip install --upgrade pip-chill pip-upgrade-outdated pre-commit
pip install -r requirements-dev.txt
pip install -r requirements.txt

echo "----- Updating the libraries installed"
# pip list --outdated --format=json | jq '.[].name' | xargs -n1 pip install -U
pip_upgrade_outdated

echo "----- Upgrading pre-commit"
pre-commit autoupdate

echo "----- Listing all the libraries installed"
function listDependecies() {
    MIN_REQ=requirements.txt
    DEV_REQ=requirements-dev.txt

    pip-chill -v >$DEV_REQ

    echo "----- Separating required libs from deployment libs"
    if [ -s $MIN_REQ ]; then
        min_md5=$(md5sum $MIN_REQ)
        required_libs=$(sed 's/==.*//' $MIN_REQ | tr '\n' '|' | sed 's/|$//' | sed 's/# //g')
        echo "----- ${#required_libs[@]} non-dev libs are required"
        echo "required_libs:" $required_libs
        egrep "$required_libs" $DEV_REQ >$MIN_REQ
        egrep -v "$required_libs" $DEV_REQ >$DEV_REQ.bak

        upd_md5=$(md5sum $MIN_REQ)
        if [[ $min_md5 = $upd_md5 ]]; then
            echo "dependencies list is complete"
            # echo "----- Adding the -r requirements.txt line to dev requirements"
            # sed '1s/^/-r requirements.txt\n/' $DEV_REQ.bak >$DEV_REQ
            mv $DEV_REQ.bak $DEV_REQ
            rm $DEV_REQ.bak
        else
            echo "dependencies list may need an update"
            listDependecies
        fi
    else
        echo "----- No libs required"
    fi
}
listDependecies

echo "----- Pre-commit checks"
pre-commit run --all-files

echo "----- The end"
echo "Mise à jour des dépendances terminée."
