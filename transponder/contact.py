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

class Contact:
    def __init__(self, name, avatar, lastMessage, unreadCounter, mentioned, mute):
        """Initialize an Contact instance.

        Attributes:
            id                  Object ID integer
            name                Name of the contact string
            avatar              URL of the contact it's avatar
            hasUnreadMessages   Boolean which indicates if the contact has
                                unread messages
            unreadCounter       Integer representing the number of unread 
                                messages
            mentioned           If the user has been mentioned boolean
            messagePreview      Last message text string
            readMessage         Last message has been read or not boolean
            receivedMessage     Last message has been received or not boolean
            mute                Mute the contact or not boolean
        """
        self.id = id(self)
        self.name = name
        self.avatar = avatar
        self.hasUnreadMessages = unreadCounter > 0
        self.unreadCounter = unreadCounter
        self.mentioned = mentioned
        self.messagePreview = lastMessage.message
        self.readMessage = lastMessage.readMessage
        self.receivedMessage = lastMessage.receivedMessage
        self.mute = mute
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Contact instance created")