from syncthing import Syncthing

# Self-defined
import platform_adapter

# Standard library
import sys, platform, json

class SyncthingFacade():
    
    def __init__(self):
        self.sync = None
        self.adapter = None
            
    def get_config(self):
        return self.sync.sys.config()

    def get_device_id(self):
        try:
            return self.sync.sys.config()['devices'][0]['deviceID']
        except Exception:
            if self.adapter:
                return self.adapter.get_device_id()
            else:
                return None
        
    def set_config(self, config):
        return self.sync.sys.set.config(config = config)

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

    def devid_to_ip(self, devid):
        discovery = self.sync.sys.discovery()

        if not devid in discovery:
            return None
        else:
            address = discovery[devid]['addresses']

            for e in address:
                if 'tcp://' in e:
                    href = e
                    break

            return href.split('/')[2].split(':')[0]

class SyncthingClient(SyncthingFacade):
    
    def __init__(self, adapter):
        SyncthingFacade.__init__(self)

        self.adapter = adapter

        try:
            self.sync = self.adapter.get_gui_hook()
        except Exception:
            pass

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
        
        try:
            toks = key.split('@')
            device_id = toks[0]
            api_key = toks[1]
        except IndexError as e:
            return 'Invalid Key.'

        # Check if the device id is valid
        if 'error' in self.sync.misc.device_id(id=device_id):
            return 'Invalid Key.'

        try:
            host = self.devid_to_ip(device_id)
            remote = SyncthingProxy(device_id, host, api_key)
            res = remote.connect()
            config = self.adapter.update_config({
                'device_id' : device_id,
                'api_key' : api_key,
                'name' : name,
                'path' : path
            })
        except KeyError as e:
            return e.message
        except Exception as e:
            print str(e)
            return 'Please fix me.'
 
    def test(self): 
        print self.devid_to_ip( 'UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        print dir(self.sync.sys.set.config)
        print self.sync.misc.device_id(id='UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        return self.sync.sys.ping()

class SyncthingProxy(SyncthingFacade):

    remote_port = 8384

    def __init__(self, device_id, host, api_key):
        SyncthingFacade.__init__(self)
        
        self.sync = Syncthing(
            api_key=api_key, 
            port=self.remote_port, 
            host=host
        )

        if not self.ping():
            raise IOError('Could not connect to %s:%s.' % (host, self.remote_port))

    def connect(self):
        config = self.get_config()       

        res = self.set_config(json.dumps(config))
        print 'Remote ' + res.text
        return

    def disconnect(self):
        return

syncthing_linux = None
syncthing_mac = None
syncthing_win = None

if platform.system() == "Linux" or platform.system() == "Linux2":
    syncthing_linux = SyncthingClient(
        platform_adapter.SyncthingLinux64()
    ) # Linux
elif platform.system() == "Darwin":
    syncthing_mac = SyncthingClient(
        platform_adapter.SyncthingMac64()
    ) # MacOSX
elif platform.system() == "Windows":
    syncthing_win = SyncthingClient(
        platform_adapter.SyncthingWin64()
    ) # TODO: Windows

def get_handler():
    handler = {
        'Linux' : syncthing_linux,
        'Darwin' : syncthing_mac,
        'Windows' : syncthing_win
    }.get(platform.system(), None)

    if not handler:
        raise Exception("%s is not currently supported." % platform.system())

    return handler
