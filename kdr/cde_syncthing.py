from syncthing import Syncthing

# Self-defined
import src_proxy
import platform_adapter

# Standard library
import subprocess 
import os, sys
import xml.etree.ElementTree as ET
import json
import hashlib
import platform


class SyncthingFacade():
    
    sync = None
    adapter = None

    def __init__(self, adapter):

        self.adapter = adapter

        try:
            self.sync = self.adapter.get_gui_hook()
        except Exception:
          pass

    def get_config(self):
        return self.sync.sys.config()
        
    def set_config(self, config):
        return self.sync.sys.set.config(config)

    def restart(self):
        self.sync.sys.set.restart();

    def start(self):    
        path = self.adapter.get_path()
        
        return self.adapter.start(path);

    def ping(self):
        # Silence stderr
        save_stderr = sys.stderr
        sys.stderr = open('trash', 'w')

        # Run command
        t = type(self.sync.sys.set.ping()) 
        sys.stderr = save_stderr

        return t == dict

    def shutdown(self):
        return self.sync.sys.set.shutdown()

    def name(self):
        try:
            return self.sync.sys.config()['devices'][0]['deviceID']
        except Exception:
            return self.adapter.get_device_id()

    def init(self, key, name, path):

        """

            1. If config.json not created:
                Create config as ~/.config/kdr/config.json
                Initialize contents in confing.json
            else
                Append new folder data to config
            
            2. Notify the remote device that this machine
                 wants to connect to it.

            Args:
                key(str): remote device-id used to identify src
                name(str): user defined name associating key 
                path(str): path to folder user wants to sync
            
            returns success or failure

        """

        try:
            config = self.adapter.create_config(key, name, path)
            res = src_proxy.connect(self.name())

            if res.status == '200':
                return 'Success' 
            else:
                raise RuntimeError(res.body)
        except Exception, e:
            print str(e)
            return 'Failure'
     
    def test(self):
        sync = Syncthing(api_key='ACWpWrFTsgME52NAA7sHFeSfbvSKcCtG', port=8384)
        print sync
        return sync.sys.ping()
                
class SyncthingFactory:
    
    syncthing_posix = None
    syncthing_mac = None
    syncthing_win = None

    def __init__(self):
        if platform.system() == "Linux" or platform.system() == "Linux2":
            self.syncthing_posix = SyncthingFacade(platform_adapter.SyncthingLinux64())
            # Linux
        elif platform.system() == "Darwin":
            self.syncthing_mac = SyncthingFacade(platform_adapter.SyncthingMac64())
            # MacOSX
        elif platform.system() == "Windows":
            self.syncthing_win = SyncthingFacade(platform_adapter.SyncthingWin64())
            # TODO: Windows

    def get_handler(self):
        handler = {
            'Linux' : self.syncthing_posix,
            'Darwin' : self.syncthing_mac,
            'Windows' : self.syncthing_win
        }.get(platform.system(), None)
        
        if not handler:
            raise Exception("%s is not currently supported." % platform.system())

        return handler

# Singleton
factory = SyncthingFactory()

def start():
    handler = factory.get_handler()

    try:
        alive = handler.ping()

    except Exception:
        alive = False

    finally:
        if not alive:
            success = handler.start()

            if not success:
                return 'An error has occurred'

            else:
                return handler.name()

    return 'KodeDrive has already been started.' 

def config():
    handler = factory.get_handler()
    
    return json.dumps(handler.get_config())

def stop():
        
    handler = factory.get_handler()

    try:
        alive = handler.ping()
    except:
        alive = False

    if not alive:
        return 'KodeDrive has already exited.'

    return handler.shutdown()

def status():
    handler = factory.get_handler()

    return 'KodeDrive is up.' if handler.ping() else 'KodeDrive is down.'

def name():
    handler = factory.get_handler()
    return handler.name()

def init(key, name, path):
    handler = factory.get_handler()
    return handler.init(key, name, path)

def test():
    handler = factory.get_handler()
    return handler.test()
