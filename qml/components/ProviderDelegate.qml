/*
*   This file is part of Transponder.
*
*   Transponder is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   Transponder is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with Transponder.  If not, see <http://www.gnu.org/licenses/>.
*/

import QtQuick 2.0
import Sailfish.Silica 1.0

ListItem {
    contentHeight: column.height + Theme.paddingLarge

    Label {
        anchors {
            verticalCenter: parent.verticalCenter
            left: parent.left
            leftMargin: Theme.horizontalPageMargin
            right: column.left
            rightMargin: Theme.paddingLarge
        }
        truncationMode: TruncationMode.Fade
        font.pixelSize: Theme.fontSizeLarge
        text: model.name
    }

    Column {
        id: column
        anchors {
            right: parent.right
            rightMargin: Theme.horizontalPageMargin
            verticalCenter: parent.verticalCenter
        }
        width: Theme.itemSizeSmall

        GlassItem {
            anchors.horizontalCenter: parent.horizontalCenter
            color: {
                if(model.installed) {
                    if(model.updatable) {
                        return "yellow"
                    }
                    return "green"
                }
                else {
                    return "red"
                }
            }
            falloffRadius: 0.15
            radius: 1.0
            cache: false
        }

        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            truncationMode: TruncationMode.Fade
            color: Theme.highlightColor
            text: model.version
        }
    }
}
