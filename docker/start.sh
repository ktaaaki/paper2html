#!/bin/bash

# paper2html/docker/start.sh
# This file is licensed under the MIT license (see LICENSE_MIT for details)
# Copyright (C) 2021 eitsupi

su ${USER_NAME} -c "python ./paper2html/paper2html/main.py --host=0.0.0.0 --watch=True"