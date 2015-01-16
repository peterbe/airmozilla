#!/bin/bash
# pwd is the git repo.
set -e

echo "Install Python dependencies"
pip install -r requirements.txt
pip install coverage
pip install flake8

echo "Creating a test database"
psql -c 'create database airmozilla;' -U postgres
