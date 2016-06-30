from syncthing import Syncthing

# Self-defined
import src_proxy
import platform_adapter

# Standard library
import sys, platform
import json, hashlib

class SyncthingFacade():
    
    remote_port = 8384

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

    def get_device_id(self):
        try:
            return self.sync.sys.config()['devices'][0]['deviceID']
        except Exception:
            return self.adapter.get_device_id()
        
    def set_config(self, config):
        return self.sync.sys.set.config(config)

    def restart(self):
        self.sync.sys.set.restart();

    def start(self):    
        path = self.adapter.get_path()
        
        return self.adapter.start(path);

    def shutdown(self):
        return self.sync.sys.set.shutdown()
        
    def ping(self):
        # Silence stderr
        save_stderr = sys.stderr
        sys.stderr = open('trash', 'w')

        # Run command
        t = type(self.sync.sys.set.ping()) 
        sys.stderr = save_stderr

        return t == dict

    def devid_to_ip(devid):
        return
        

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
                key(str): remote deviceId@apiKey used to identify src
                name(str): user defined name associating key 
                path(str): path to folder user wants to sync
            
            returns success or failure

        """
        
        toks = key.split('@')
        device_id = toks[0]
        
        # Check if the device id is valid
        if 'error' in self.sync.misc.device_id(id=device_id):
            return 'Invaid Key.'

        api_key = toks[1]

        remote_sync = Syncthing(api_key=api_key, port=self.remote_port, host='1')

        # Check if api_key is valid

        try:

            config = self.adapter.create_config(key, name, path)
            res = src_proxy.connect(self.name())

            if res.status == '200':
                return "%s is now synchronizing with %s" % (path, key)
            else:
                raise RuntimeError(res.body)

        except Exception, e:
            print str(e)
            return 'Failure'
     
    def test(self):
        print Syncthing
        print dir(self.sync.misc)
        print self.sync.misc.device_id(id='UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        return self.sync.sys.ping()
                
class SyncthingFactory:
    
    syncthing_linux = None
    syncthing_mac = None
    syncthing_win = None

    def __init__(self):

        if platform.system() == "Linux" or platform.system() == "Linux2":
            self.syncthing_linux = SyncthingFacade(
                platform_adapter.SyncthingLinux64()
            ) # Linux
        elif platform.system() == "Darwin":
            self.syncthing_mac = SyncthingFacade(
                platform_adapter.SyncthingMac64()
            ) # MacOSX
        elif platform.system() == "Windows":
            self.syncthing_win = SyncthingFacade(
                platform_adapter.SyncthingWin64()
            ) # TODO: Windows

    def get_handler(self):
        handler = {
            'Linux' : self.syncthing_linux,
            'Darwin' : self.syncthing_mac,
            'Windows' : self.syncthing_win
        }.get(platform.system(), None)
        
        if not handler:
            raise Exception("%s is not currently supported." % platform.system())

        return handler

# Singleton
factory = SyncthingFactory()

def start():

    try:
        handler = factory.get_handler()
        alive = handler.ping()
    except Exception as e:
        alive = False
    
    if not alive:
        success = handler.start()   

        if not success:
            return e if e else 'KodeDrive could not be started.'
        else:
            return handler.name()
    else:
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
    return handler.get_device_id()

def init(key, name, path):
    handler = factory.get_handler()
    return handler.init(key, name, path)

def test():
    handler = factory.get_handler()
    return handler.test()
