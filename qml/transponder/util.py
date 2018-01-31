# -*- coding: utf-8 -*-
#
#   This file is part of Transponder.
#
#   Transponder is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Transponder is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Transponder.  If not, see <http://www.gnu.org/licenses/>.

"""
Transponder is a Sailfish OS application that provide access to different 
messaging providers using Python plugins.
"""

import json
import logging
import time
import sys
import os
from random import randint

_logger = logging.getLogger(__name__)

HTTP_OK = 200

def read_json(file):
    try:
        data = json.load(open(file, "r"))
        _logger.debug("Reading JSON file succesfully")
        return data
    except Exception:
        _logger.error("Can't read JSON file: {0}".format(str(file)))
        return {}
        
def save_binary_file(path, data):
    try:
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(path, "wb") as f:
            f.write(data)
        _logger.debug("Written file {0} succesfull".format(path))
        return True
    except IOError as e:
        _logger.error("I/O error({0}): {1} for file: {2}".format(e.errno, e.strerror, path))
        return False
    except: #handle other exceptions such as attribute errors
        _logger.error("Unexpected error:", sys.exc_info()[0])
        return False


def generate_id():
    return int(time.time() + randint(0, 100000))