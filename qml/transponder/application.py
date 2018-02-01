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

from transponder import util, paths
from transponder.provider import Provider
from transponder.sdk import SDK
import logging
import pyotherside

PROVIDERS_FILE = paths.TRANSPONDER_DIR + "/data/providers.json"

__all__ = ("Application")

PROVIDER_REMOVE = 0
PROVIDER_INSTALL = 1
PROVIDER_UPDATE = 2

class Application:
    """ Application contains all the application APIs of Transponder. 
        This instance acts like the Controller in MVC. Every class needs a
        pointer to this instance. In QML it's available using a global 
        variable.
    """
    
    def __init__(self):
        """Initialize an Application instance."""
        self.id = util.generate_id()
        self._logger = logging.getLogger(__name__)
        self.providers = []
        supported_providers = util.read_json(PROVIDERS_FILE)["providers"]
        if supported_providers: # valid data
            for p in supported_providers:
                sdk = SDK(self, p["name"], p["url"], p["version"], p["module"], p["hash256"])
                self.providers.append(Provider(self, p["name"], sdk))
        else:
            self._logger.error("Invalid data from provider.json")
        self._logger.debug("Application instance created")
        
    def get_available_providers(self):
        providersList = []
        for p in self.providers:
            p.sdk.check_for_update()
            data = {
            "id": p.id, 
            "name": p.name, 
            "module": p.sdk.module_name, 
            "installed": p.sdk.installed, 
            "updatable": p.sdk.updatable, 
            "verified": p.sdk.verified,
            "version": p.sdk.installed_version
            }
            providersList.append(data) 
        return providersList
        
    def install_provider(self, module):
        return self._manage_provider(module, PROVIDER_INSTALL)
                
    def remove_provider(self, module):
        return self._manage_provider(module, PROVIDER_REMOVE)
        
    def update_provider(self, module):
        return self._manage_provider(module, PROVIDER_UPDATE)
        
    def send_signal(self, name, data=""):
        pyotherside.send(name, data)
        
    def _manage_provider(self, module, cmd):
        for p in self.providers:
            if(p.sdk.module_name == module):
                if(cmd == PROVIDER_REMOVE):
                    p.sdk.remove()
                elif(cmd == PROVIDER_INSTALL):
                    p.sdk.install()
                elif(cmd == PROVIDER_UPDATE):
                    p.sdk.update()
                else:
                    self._logger.error("Unknown provider SDK command")
                break;
        return self.get_available_providers()
        
    
