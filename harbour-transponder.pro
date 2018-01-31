# NOTICE:
#
# Application name defined in TARGET has a corresponding QML filename.
# If name defined in TARGET is changed, the following needs to be done
# to match new name:
#   - corresponding QML filename must be changed
#   - desktop icon filename must be changed
#   - desktop filename must be changed
#   - icon definition filename in desktop file must be changed
#   - translation filenames have to be changed

# The name of your application
TARGET = harbour-transponder

CONFIG += sailfishapp_qml

# DBus support
QT += dbus

# Disable debug and warning messages while releasing for security reasons
CONFIG(release, debug|release):DEFINES += QT_NO_DEBUG_OUTPUT \
QT_NO_WARNING_OUTPUT

DISTFILES += qml/harbour-transponder.qml \
    qml/cover/CoverPage.qml \
    qml/pages/FirstPage.qml \
    rpm/harbour-transponder.changes.in \
    rpm/harbour-transponder.changes.run.in \
    rpm/harbour-transponder.spec \
    rpm/harbour-transponder.yaml \
    translations/*.ts \
    transponder/*.py \
    transponder/data/*.json \
    harbour-transponder.desktop \
    qml/components/API.qml

SAILFISHAPP_ICONS = 86x86 108x108 128x128

# APP_VERSION retrieved from .spec file
DEFINES += APP_VERSION=\"\\\"$${VERSION}\\\"\"

# to disable building translations every time, comment out the
# following CONFIG line
CONFIG += sailfishapp_i18n \
    sailfishapp_i18n_idbased

# German translation is enabled as an example. If you aren't
# planning to localize your app, remember to comment out the
# following TRANSLATIONS line. And also do not forget to
# modify the localized app name in the the .desktop file.
TRANSLATIONS += translations/harbour-transponder.ts

RESOURCES += \
    resources/resources.qrc
