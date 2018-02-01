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
import Nemo.Notifications 1.0
import "../components"

Page {
    Component.onCompleted: api.getProviders()

    ListModel {
        id: providersListModel
    }

    Connections {
        target: api
        onProvidersChanged: {
            console.log(JSON.stringify(api.providers))
            providersListModel.clear()
            for(var i=0; i < api.providers.length; i++) {
                providersListModel.append(api.providers[i])
            }
        }

        onProviderDownloadStarted: {
            downloadProgress.value = 0.0
            downloadProgress.indeterminate = true
            downloadProgress.opacity = 1.0
        }
        onProviderDownloadProgress: {
            downloadProgress.indeterminate = false
            downloadProgress.value = Math.round(progress)
        }
        onProviderDownloadFinished: downloadProgress.opacity = 0.0
        onProviderCorrupted: errorNotify.prepare("Provider corrupted", "Can't use your provider module, try to update the module")
        onProviderDownloadFailed: errorNotify.prepare("Downloading failed", "Can't download your provider module, please check your network connection")
        onProviderRemoveFailed: errorNotify.prepare("Removing failed", "Can't remove your provider module, please try again later")
        onProviderInstallFailed: errorNotify.prepare("Installation failed", "Can't install your provider module, please try again later")
    }

    Notification {
        id: errorNotify
        appIcon: "image://theme/icon-lock-warning"
        urgency: Notification.Critical

        function prepare(summary, body) {
            console.debug("Preparing error notification")
            errorNotify.close() // Close any previous notifications
            errorNotify.previewSummary = summary
            errorNotify.previewBody = body
            errorNotify.summary = summary
            errorNotify.body = body
            errorNotify.publish()
            console.debug("Error notification published")
        }
    }

    SilicaFlickable {
        width: parent.width
        height: column.height

        Column {
            id: column
            width: parent.width

            PageHeader {
                title: "Settings"

                BusyIndicator {
                    id: busy
                    size: BusyIndicatorSize.Small
                    anchors {
                        verticalCenter: parent.verticalCenter
                        left: parent.left
                        leftMargin: Theme.paddingLarge*3
                    }
                    running: api.busy
                }
            }

            SectionHeader { text: "Providers" }

            ProgressBar {
                id: downloadProgress
                width: parent.width
                maximumValue: 100
                valueText: value > 0.0? value + " %": ""
                label: "Downloading..."
                opacity: 0.0
                visible: opacity > 0.0
                Behavior on opacity { FadeAnimator {} }
            }

            SilicaListView {
                width: parent.width
                height: contentHeight
                model: providersListModel
                delegate: ProviderDelegate {
                    width: ListView.view.width
                    enabled: !downloadProgress.visible
                    opacity: enabled? 1.0: 0.7
                    menu: ContextMenu {
                        MenuItem {
                            text: "Install"
                            onClicked: api.installProvider(model)
                            visible: !model.installed
                        }
                        MenuItem {
                            text: "Remove"
                            onClicked: api.removeProvider(model)
                            visible: model.installed
                        }
                        MenuItem {
                            text: "Update"
                            onClicked: api.updateProvider(model)
                            visible: model.installed && model.updatable
                        }
                    }
                }
            }
        }
    }
}
