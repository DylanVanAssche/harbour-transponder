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

    Connections {
        target: api
        // Figure out how auth is done: phone, host, ...
    }

    SilicaFlickable {
        anchors.fill: parent
        contentHeight: column.height

        Column {
            id: column
            width: parent.width

            PageHeader {
                title: "Add new account"
            }

            Row {
                anchors {
                    left: parent.left
                    leftMargin: Theme.horizontalPageMargin
                    right: parent.right
                    rightMargin: Theme.horizontalPageMargin
                }
                spacing: Theme.paddingLarge
                height: Math.max(icon.height, Theme.itemSizeExtraLarge)

                Image {
                    id: icon
                    width: Theme.itemSizeMedium
                    height: width
                    anchors.verticalCenter: parent.verticalCenter
                    asynchronous: true
                    cache: true
                    source: "https://raw.githubusercontent.com/DylanVanAssche/harbour-matriksi/master/icons/256x256/harbour-matriksi.png"
                }

                Label {
                    width: parent.width - icon.width - parent.spacing
                    anchors.verticalCenter: parent.verticalCenter
                    font.pixelSize: Theme.fontSizeHuge
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    truncationMode: TruncationMode.Fade
                    text: "Matrix.org"
                }
            }

            TextField {
                id: host
                anchors { left: parent.left; right: parent.right }
                label: "Host"; placeholderText: label
                EnterKey.enabled: text || inputMethodComposing
                EnterKey.iconSource: "image://theme/icon-m-enter-next"
                EnterKey.onClicked: email.focus = true
                inputMethodHints: Qt.ImhUrlCharactersOnly
            }

            TextField {
                id: email
                anchors { left: parent.left; right: parent.right }
                label: "Email address"; placeholderText: label
                EnterKey.enabled: text || inputMethodComposing
                EnterKey.iconSource: "image://theme/icon-m-enter-next"
                EnterKey.onClicked: password.focus = true
                inputMethodHints: Qt.ImhEmailCharactersOnly
            }

            TextField {
                id: phonenumber
                anchors { left: parent.left; right: parent.right }
                label: "Phone number"; placeholderText: label
                EnterKey.enabled: text || inputMethodComposing
                EnterKey.iconSource: "image://theme/icon-m-enter-next"
                EnterKey.onClicked: password.focus = true
                inputMethodHints: Qt.ImhDigitsOnly
            }

            TextField {
                id: phonecode
                anchors { left: parent.left; right: parent.right }
                label: "SMS code"; placeholderText: label
                EnterKey.enabled: text || inputMethodComposing
                EnterKey.iconSource: "image://theme/icon-m-enter-next"
                EnterKey.onClicked: password.focus = true
                inputMethodHints: Qt.ImhDigitsOnly
            }

            PasswordField {
                id: password
                anchors { left: parent.left; right: parent.right }
                label: "Password"; placeholderText: label
                EnterKey.enabled: text || inputMethodComposing
                EnterKey.iconSource: "image://theme/icon-m-enter-next"
                EnterKey.onClicked: console.debug("Creating account...")
            }
        }
    }
}
