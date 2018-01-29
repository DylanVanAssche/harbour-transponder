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
import "../components"

Page {
    id: page

    SilicaListView {
        id: matchesListView
        anchors.fill: parent
        delegate: ContactsDelegate {
            id: contact
            width: ListView.view.width
            onRemoved: console.debug("Remove item") //api.remove(model.matchId)
            onClicked: pageStack.push(
                           Qt.resolvedUrl("MessagingPage.qml"),
                           {
                            // Arguments here
                           }
                           )
            menu: ContextMenu {
                MenuItem {
                    //% "Remove"
                    text: qsTrId("transponder-remove")
                    onClicked: contact.remove()
                }
            }
        }

        VerticalScrollDecorator {}
    }

    ViewPlaceholder {
        id: noContactsText
        anchors.centerIn: parent
        //% "No contacts!"
        text: qsTrId("transponder-no-matches")
        enabled: false
    }

    BusyIndicator {
        id: busyStatus
        anchors.centerIn: parent
        size: BusyIndicatorSize.Large
        running: Qt.application.active
    }
}

