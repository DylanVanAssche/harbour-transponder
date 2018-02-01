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
import io.thp.pyotherside 1.3

// Needs handling for network lost using DBUS

Python {
    property var providers
    property bool busy: true
    signal pythonReady()
    signal providerCorrupted()
    signal providerDownloadFailed()
    signal providerRemoveFailed()
    signal providerInstallFailed()
    signal providerDownloadStarted()
    signal providerDownloadProgress(int progress)
    signal providerDownloadFinished()

    id: api
    onReceived: console.warn("Unhandled Python signal: " + data)
    onError: console.error("Python error: " + traceback)
    Component.onCompleted: {
        // Transponder module path
        addImportPath(Qt.resolvedUrl(".."));

        // Requests module
        addImportPath(Qt.resolvedUrl("../transponder/requests"));
        addImportPath(Qt.resolvedUrl("../transponder/chardet"));
        addImportPath(Qt.resolvedUrl("../transponder/idna"));
        addImportPath(Qt.resolvedUrl("../transponder/python-certifi"));
        addImportPath(Qt.resolvedUrl("../transponder/urllib3"));

        // Import our main module
        importModule("transponder", function() {
            pythonReady()
            api.busy = false
        });

        // Enable handlers
        setHandler("provider-error-corrupt", function () {
            console.error("Provider install is corrupted")
            providerCorrupted()
        });
        setHandler("provider-error-download", function () {
            console.error("Provider download failed")
            providerDownloadFailed()
        });
        setHandler("provider-error-install", function () {
            console.error("Provider installation failed")
            providerInstallFailed()
        });
        setHandler("provider-error-remove", function () {
            console.error("Provider removing failed")
            providerRemoveFailed()
        });
        setHandler("provider-download-started", function () {
            console.error("Provider download started")
            providerDownloadStarted()
        });
        setHandler("provider-download-progress", function (progress) {
            console.error("Provider download progress: " + progress)
            providerDownloadProgress(progress)
        });
        setHandler("provider-download-finished", function () {
            console.error("Provider download finished")
            providerDownloadFinished()
        });
    }
    
    // Returns all the available providers in Transponder and if they are installed or not
    function getProviders() {
        console.debug("Retrieving providers")
        api.busy = true
        call("transponder.app.get_available_providers", [], function(providers) {
            console.debug("Providers retrieved: " + JSON.stringify(providers))
            api.providers = providers;
            api.busy = false
        })
    }

    // Install a given provider
    function installProvider(provider) {
        console.debug("Installing provider SDK: " + provider.name)
        api.busy = true
        call("transponder.app.install_provider", [provider.module], function(providers) {
            api.providers = providers;
            api.busy = false
        })
    }

    // Remove a given provider
    function removeProvider(provider) {
        console.debug("Removing provider SDK: " + provider.name)
        api.busy = true
        call("transponder.app.remove_provider", [provider.module], function(providers) {
            api.providers = providers;
            api.busy = false
        })
    }

    // Update a given provider
    function updateProvider(provider) {
        console.debug("Updating provider SDK: " + provider.name)
        api.busy = true
        call("transponder.app.update_provider", [provider.module], function(providers) {
            api.providers = providers;
            api.busy = false
        })
    }
}
