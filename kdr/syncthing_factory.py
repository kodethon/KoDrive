from py_syncthing_adapter import Syncthing

# Self-defined
import platform_adapter

# Standard library
import sys, platform, time
import socket, json

class SyncthingFacade():
    
    def __init__(self):
        self.sync = None
        self.adapter = None
            
    def get_config(self):
        return self.sync.sys.config()

    def get_device_id(self):
        try:
            return self.sync.sys.status()['myID']
        except Exception:
            if self.adapter:
                return self.adapter.get_device_id()
            else:
                return None
        
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
        try:
            t = type(self.sync.sys.set.ping()) 
            sys.stderr = save_stderr
            
        except:
            return False

        return t == dict

    def devid_to_ip(self, devid, wait = True):

        if not wait:
            try:
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
            except Exception:
                return None
        else:
            count = 1
            host = None

            # Wait for changes to take effect
            while count <= 5:

                print "Attempt %i to discover device." % count

                try:
                    host = self.devid_to_ip(devid, False)           
                except Exception:
                    pass

                if not host:
                    time.sleep(1.5)
                    count += 1
                else:
                    print 'Device successfully discovered!'
                    return host

            return None

    def new_device(self, config, devid):

        record = {
            'deviceId' : devid,
            'name' : 'Unknown',
            'compression' : 'metadata',
            'introducer' : False,
            'certName' : '',
            'address' : ['dynamic']
        }

        config['devices'].append(record)
                
    def device_exists(self, client_devid, config=None):

        if not config:
            config = self.get_config()       

        # Check to see if device already exists
        for e in config['devices']:
            device_id = e['deviceID']
            
            if device_id == client_devid:
                return True
        
        return False

    def folder_exists(self, object, config = None):

        if not config:
            config = self.get_config()
        
        exists = False

        # list of folders
        folders = config['folders']

        for f in folders:
            n = 0
            d = 0

            for k in object:
                if object[k] == f[k]:
                    n += 1

                d += 1

            if n == d:
                exists = True
                break

        return exists

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
            config = self.get_config()

            if not self.device_exists(device_id):
                self.new_device(config, device_id)
                self.set_config(config)
                self.restart()
            
            host = self.devid_to_ip(device_id)
             
            # Request remote to share its folder with us
            remote = SyncthingProxy(device_id, host, api_key)
            
            # Hack to fix odd self.sync object change
            self.sync = self.adapter.get_gui_hook()
            
            remote_folder = remote.request_folder(self.get_device_id())
            
            self.sync = self.adapter.get_gui_hook()
            # Save the folder data into syncthing config
            self.acknowledge(remote_folder, path)
            self.restart()
            
            # Save folder data into kdr config
            config = self.adapter.update_config({
                'device_id' : device_id,
                'api_key' : api_key,
                'name' : name,
                'path' : path
            })

            return 'Success'
        except KeyError as e:
            return e.message
        except ValueError as e:
            return e.message
        #except Exception as e:
        #   print e.message
        #    return 'Big bad un-expected booboo.'

    # Commit the shared remote folder data
    # into local config.xml file
    def acknowledge(self, remote_folder, local_path):
        config = self.get_config()
        
        if self.folder_exists({
            'id' : remote_folder['id']
        }, config):
            raise ValueError('Folder already exists.')

        remote_folder['path'] = local_path
        remote_folder['label'] = 'sync'
        config['folders'].append(remote_folder)

        return self.set_config(config)
 
    def test(self): 

        print self.sync.sys.status()['myID']
        return
        print self.devid_to_ip( 'UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        print dir(self.sync.sys.set.config)
        print self.sync.misc.device_id(id='UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        return self.sync.sys.ping()

class SyncthingProxy(SyncthingFacade):

    remote_port = 8384

    def __init__(self, device_id, host, api_key):
        SyncthingFacade.__init__(self)
        
        self.device_id = device_id
        self.host = host
        self.api_key = api_key
        self.sync = Syncthing(
            api_key=api_key, 
            port=self.remote_port, 
            host=host
        )
        
        # If remote host can't be detected, throw a tantrum >:/
        if not self.ping():
            raise IOError('Could not connect to %s:%s.' % (host, self.remote_port))

    def request_folder(self, client_devid):
        self.sync = Syncthing(
            api_key=self.api_key, 
            port=self.remote_port, 
            host=self.host
        )
        config = self.get_config()       
        
        self.new_device(config, client_devid)

        config['folders'][0]['devices'].append({
            'deviceID' : client_devid
        })

        self.set_config(config)
        self.restart()

        return config['folders'][0]

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
