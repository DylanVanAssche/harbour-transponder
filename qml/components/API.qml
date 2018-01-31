import QtQuick 2.0
import Sailfish.Silica 1.0
import io.thp.pyotherside 1.3

// Needs handling for network lost using DBUS

Python {
    property var providers
    property bool busy: true
    signal pythonReady()

    id: api
    onReceived: console.warn("Unhandled Python signal: " + data)
    onError: console.error("Python error: " + traceback)
    Component.onCompleted: {
        // Transponder module path
        addImportPath(Qt.resolvedUrl(".."));

        // Dependencies for Requests module
        addImportPath(Qt.resolvedUrl("../transponder/chardet"));
        addImportPath(Qt.resolvedUrl("../transponder/idna"));
        addImportPath(Qt.resolvedUrl("../transponder/python-certifi"));
        addImportPath(Qt.resolvedUrl("../transponder/urllib3"));

        // Import our main module
        importModule("transponder", function() {
            pythonReady()
            api.busy = false
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
