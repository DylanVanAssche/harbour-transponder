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

import os
import logging
import importlib
import sys
from transponder import paths, util
from transponder.requests import requests

class SDK:
    def __init__(self, app, name, url, version, module_name):
        """
            Creates a SDK instance
        """
        self.id = util.generate_id()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.url = url
        self.required_version = version
        self.installed_version = None
        self.module_name = module_name
        self.module = None
        self.path = "{0}/{1}.zip".format(paths.TRANSPONDER_SDK_DIR, self.module_name) # All SDKs are ZIP files
        self.installed = os.path.exists(self.path)
        self.updatable = False
        
        self.get_installed_version()
        self.check_for_update()
        
    def check_for_update(self):
        """
            Check for updates for the SDK, this method updates the <updatable>
            property if needed
        """
        if(self.installed):
                self.get_installed_version()
                self.updatable = self.installed_version != self.required_version   
        else:
            self.updatable = False
            self._logger.debug("{0} is not installed, no updates".format(self.module_name))
            
    def get_installed_version(self):
        """
            Retrieves the installed version for the SDK and updates it if 
            needed
        """
        if(self.installed):
            try:
                sys.path.append(self.path) # Add module location to PYTHONPATH
                if(self.module == None):
                    self.module = importlib.import_module(self.module_name) # Try to import it
                else:
                    importlib.reload(self.module) # When already imported, reload due update
                self.installed_version = self.module.__version__
                self._logger.debug("{0} imported succesfully with version {1}".format(self.module_name, self.installed_version))
            except ImportError:
                self._logger.error("Import error for module: {0}".format(self.module_name))
        else:
            self.installed_version = ""
        return self.installed_version
        
    def install(self):
        """
            Installs the SDK by downloading it from the url in the 
            providers.json file
        """
        if(not(self.installed)):
            self._logger.debug("{0} not installed, installing now".format(self.name))
            response = requests.get(self.url)
            self._logger.debug("Finished download with status code: {0}".format(response.status_code))
            if(response.status_code == util.HTTP_OK and util.save_binary_file(self.path, response.content)):
                self.installed = os.path.exists(self.path)
                self.get_installed_version() # Update version
                self.check_for_update() # Update updatable property
                self._logger.debug("Finished installation: {0}".format(self.name))
            else:
                self._logger.error("Installation: {0} failed!".format(self.name))
                self.app.send_signal("sdk_install_error")
        else:
            self._logger.debug("{0} already installed".format(self.name))
            
    def remove(self):
        """
            Removes the SDK from Transponder
        """
        if(self.installed):
            self._logger.debug("{0} installed, removing now".format(self.name))
            try:
                os.remove(self.path)
                self.installed = os.path.exists(self.path)
                self.check_for_update()
                self.get_installed_version()
            except:
                self.app.send_signal("sdk_remove_error")
        else:
            self._logger.debug("{0} not installed, can't remove".format(self.name))
            
    def update(self):
        """
            Updates the SDK if possible by removing the old one and 
            downloading the new one. The required version is supplied in the
            providers.json file
        """
        if(self.installed and self.updatable):
            self._logger.debug("{0} updating".format(self.name))
            self.remove()
            self.install()
        else:
            self._logger.debug("{0} not installed, can't update".format(self.name))
            
    
            