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

import logging

class Message:
    def __init__(self, message, timestamp, read, received, author):
        """Initialize an Message instance.
        
        Attributes:
            id          Object ID integer
            message     Message text string
            timestamp   Datetime object containing the timestamp of the message
            read        Boolean which indicates if the message has been read
            received    Boolean which indicates if the message has been received
            author      Name of the author string
        """
        self.id = id(self)
        self.message = message
        self.timestamp = timestamp
        self.read = read
        self.received = received
        self.author = author
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Message instance created")