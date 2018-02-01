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
import multiprocessing as mp
import queue
import time
from threading import Timer
from transponder import paths, util

class SDK:
    def __init__(self, app, name, url, version, module_name, hashcode):
        """
            Creates a SDK instancepython Thread Queue
        """
        self.id = util.generate_id()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self._worker = None
        self.name = name
        self.url = url
        self.required_version = version
        self.installed_version = ""
        self.module_name = module_name
        self.module_hash = hashcode
        self.module = None
        self.client = None
        self.path = "{0}/{1}.zip".format(paths.TRANSPONDER_SDK_DIR, self.module_name) # All SDKs are ZIP files
        self.installed = False
        self.updatable = False
        self.verified = False
        
        self.check_for_update() # Init further and checks for updates
        
    def check_for_update(self):
        """
            Check for updates for the SDK, this method updates the <updatable>
            property if needed
        """
        self.installed = os.path.exists(self.path)
        if(self.installed):
            self.get_installed_version()
            self.updatable = self.installed_version != self.required_version  
        else:
            self._logger.debug("{0} is not installed, no updates".format(self.module_name))
            self.updatable = False
        return self.updatable
            
    def get_installed_version(self):
        """
            Retrieves the installed version for the SDK and updates it if 
            needed
        """
        self.installed = os.path.exists(self.path)
        self.verify_install()
        if(self.installed and self.verified):
            try:
                sys.path.append(self.path) # Add module location to PYTHONPATH
                self._logger.debug("Module {0} path: {1}".format(self.name, self.module_name))
                if(self.module == None):
                    self.module = importlib.import_module(self.module_name) # Try to import it
                else:
                    importlib.reload(self.module) # When already imported, reload due update
                self.installed_version = self.module.__version__
                self.client = self.module.client # Connect module handler to SDK client handler
                self._logger.debug("{0} imported succesfully with version {1}".format(self.module_name, self.installed_version))
            except ImportError:
                self._logger.error("Import error for module: {0}".format(self.module_name))
                self.app.send_signal("provider-error-corrupt")
            except AttributeError:
                self._logger.error("Imported module: {0} hasn't the required client attribute".format(self.module_name))
                self.app.send_signal("provider-error-corrupt")
            except:
                self._logger.error("Importing module {0} failed due unknown error".format(self.module_name))
                self.app.send_signal("provider-error-corrupt")
        else:
            self.installed_version = ""
        return self.installed_version
        
    def install(self):
        """
            Installs the SDK by downloading it from the url in the 
            providers.json file
        """
        if(not(self.installed)):
            self._logger.debug("{0} not installed, installing now".format(self.module_name))
            q = mp.Queue() # Create queue to save the request
            self._worker = mp.Process(target=util.save_binary_stream, args=(self.url, self.path, q), daemon=True) # Create a new process
            self._worker.start() # Start the worker
            self.app.send_signal("provider-download-started")
            timeout = Timer(util.HTTP_TIMEOUT, self.cancel_install)
            timeout.start()
            response = None
            hashcode = None
            while(timeout.is_alive()):
                try:
                    msg = q.get()
                    if isinstance(msg, float): # progress state
                        self.app.send_signal("provider-download-progress", msg)
                    elif isinstance(msg, str): # progress state
                        self.app.send_signal("provider-download-integritycheck", msg)
                        hashcode = msg
                    else: # response completely received
                        response = msg
                        timeout.cancel()
                        timeout.join()
                        self.app.send_signal("provider-download-finished")
                        self._logger.debug("Finished download with status code: {0}".format(response.status_code))
                        break;
                except queue.Empty:
                    time.sleep(1) # Try again in 1 sec
            
            self.installed = os.path.exists(self.path)            
            self.verify_install(hashcode)
            self.get_installed_version() # Update version
            self.check_for_update() # Update updatable property            
            
            if(response.status_code != util.HTTP_OK): # Network error
                self.app.send_signal("provider-error-download")
            elif(not(self.installed)): # Saving error
                self.app.send_signal("provider-error-install")
                
            self._logger.debug("Finished installation: {0}".format(self.module_name))
            self.app.send_signal("provider-download-installed")
        else:
            self._logger.debug("{0} already installed".format(self.module_name))
            
    def cancel_install(self):
        if self._worker.is_alive():
            self.app.send_signal("provider-error-timeout")
            self._worker.join() # Avoid zombie processes            
            self._worker.terminate() # Kill worker
        
    def verify_install(self, hashcode=""):
        self.installed = os.path.exists(self.path)
        self.app.send_signal("Module path", self.path)
        if(self.installed):
            self._logger.debug("Module hash: {0}, downloaded hash: {1}".format(self.module_hash, hashcode))         
            
            if len(hashcode) == 0: # no hashcode provided, read file first            
                data, hashcode = util.read_binary_file(self.path)
                
            self.app.send_signal("Module hash", self.module_hash)
            self.app.send_signal("Download hash", hashcode)   
                
            if(self.module_hash == hashcode):
                self.app.send_signal("Verified hash OK")
                self.verified = True
        else:
            self.app.send_signal("Module hash NOT INSTALLED", self.module_hash)
            self.verified = False
        return self.verified
            
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
                self._logger.error("Removing module {0} failed".format(self.module_name))
                self.app.send_signal("provider-error-remove")
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
            