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
import requests
import hashlib
from random import randint

_logger = logging.getLogger(__name__)

HTTP_OK = 200
HTTP_TIMEOUT = 30
CHUNCK_SIZE = 1024
ID_RANDOM_MAX = 1000000

def read_json(file):
    try:
        with open(file, "r") as f:
            data = json.load(f)
        _logger.debug("Reading JSON file succesfully")
        return data
    except Exception:
        _logger.error("Can't read JSON file: {0}".format(str(file)))
        return False
        
def read_binary_file(file):
    hashcode = hashlib.sha256()
    with open(file, "rb") as f:
        data = f.read()
        hashcode.update(data)
    return data, hashcode.hexdigest()
        
def save_binary_stream(url, path, queue):
    # Retrieve file as stream
    response = requests.get(url, stream=True)
    hashcode = hashlib.sha256()    
    
    # Loop through the stream and save it if success
    if(response.status_code == HTTP_OK):
        try:
            size = float(response.headers["Content-length"])
            directory = os.path.dirname(path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
            progress = 0
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNCK_SIZE): 
                    if chunk: # filter out keep-alive new chunks
                        percentage = 100*(progress/size)
                        queue.put(percentage)
                        progress += CHUNCK_SIZE
                        hashcode.update(chunk)
                        f.write(chunk)
            _logger.debug("Written file {0} succesfull".format(path))
        except IOError as e:
            _logger.error("I/O error({0}): {1} for file: {2}".format(e.errno, e.strerror, path))
        except: #handle other exceptions such as attribute errors
            _logger.error("Unexpected error:", sys.exc_info()[0])
    
    # Return the hascode and response with the queue
    queue.put(hashcode.hexdigest())
    queue.put(response)

def generate_id():
    return int(time.time() + randint(0, ID_RANDOM_MAX))