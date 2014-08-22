#!/bin/bash

sudo apt-get update
sudo apt-get install git-core python3
git clone https://github.com/Cal-CS-61A-Staff/ok.git
sudo pip install --upgrade google-api-python-client
cd ok/autograder/compute_engine

python3 autograder.py
