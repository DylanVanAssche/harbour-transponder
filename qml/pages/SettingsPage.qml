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
                        leftMargin: Theme.paddingLarge
                    }
                    running: api.busy
                }
            }



            SectionHeader { text: "Providers" }

            SilicaListView {
                width: parent.width
                height: contentHeight
                model: providersListModel
                delegate: ProviderDelegate {
                    width: ListView.view.width
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
