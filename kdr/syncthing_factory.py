from py_syncthing_adapter import Syncthing

# Self-defined
import platform_adapter

# Standard library
import sys, platform, time
import socket, json

class SyncthingFacade():
    
    def __init__(self, **kwargs):
    
        if 'sync' in kwargs:
        	self.sync = kwargs['sync'] 

        if 'adapter' in kwargs:
        	self.adapter = kwargs['adapter']
            
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

    def scan(self, path):
    	
        if not path[len(path) - 1] == '/':
        	path += '/'

        folder = self.find_folder({
        	'path' : path
        }) 

        if not folder:
        	raise IOError(path + ' is not being synchronized.')
        else:
        	return self.sync.db.set.scan(folder=folder['id'])

    def completion(self, path):

        if not path[len(path) - 1] == '/':
        	path += '/'

        folder = self.find_folder({
        	'path' : path
        })

        device_id = self.get_device_id()
        res = self.sync.db.completion(device=device_id, folder=folder)
	
        return res['completion']
		
    def start(self):    
        path = self.adapter.get_path()
        
        return self.adapter.start(path);

    def shutdown(self):
        return self.sync.sys.set.shutdown()
        
    def ping(self):
        
        # Run command
        try:
            t = type(self.sync.sys.ping()) 
        except:
            return False

        return t == dict

# UTILS

    def encode_key(self):
    	config = self.get_config()
    	api_key = config['gui']['apiKey']
    	devid = self.get_device_id()
    	key = "%s@%s" % (devid, api_key)

    	return base64.b64encode(key)
    	
    def decode_key(self, encoded_key):
    	base64_key = "".join(encoded_key.split())
    	return base64.b64.decode(base64_key)

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
            count = 0
            host = None

            # Wait for changes to take effect
            while count <= 5:
                
                print "Attempt %i to discover device." % count

                host = self.devid_to_ip(devid, False)           

                if not host:
                    time.sleep(1.5)
                    count += 1
                else:
                    print 'Device successfully discovered!'
                    return host

            return None

    def new_device(self, **kwargs):

        if not 'hostname' in kwargs: 
            kwargs['hostname'] = 'Unknown'

        record = {
            'deviceId' : kwargs['device_id'],
            'name' : (kwargs['hostname'] or 'Unknown'),
            'compression' : 'metadata',
            'introducer' : False,
            'certName' : '',
            'address' : ['dynamic']
        }

        kwargs['config']['devices'].append(record)
                
    def device_exists(self, client_devid, config=None):

        if not config:
            config = self.get_config()       

        return self.find_device(client_devid, config) != None

    def find_device(self, client_devid, config=None):
        
        if not config:
            config = self.get_config()

        for d in config['devices']:
            device_id = d['deviceID']
            
            if device_id == client_devid:
                return d

    def find_folder(self, object, config=None):
			
        if not config:
            config = self.get_config()
        
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
                return f 

    def folder_exists(self, object, config = None):

        if not config:
            config = self.get_config()
        
        return self.find_folder(object, config) != None

class SyncthingClient(SyncthingFacade):
    
    def __init__(self, adapter):
        SyncthingFacade.__init__(self)

        self.adapter = adapter

        try:
            self.sync = self.adapter.get_gui_hook()
        except Exception:
            pass

    def init(self, key, name, local_path):

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
                self.new_device(config=config, device_id=device_id)
                self.set_config(config)
                self.restart()
            
            host = self.devid_to_ip(device_id)

            # Request remote to share its folder with us
            remote = SyncthingProxy(device_id, host, api_key)
            remote_config = remote.request_folder(
                self.hostname(),    
                self.get_device_id()
            )
            
            # Save the folder data into syncthing config
            self.acknowledge(
                remote.hostname(remote_config), 
                device_id,
                remote_config['folders'][0], 
                local_path
            )

            self.restart()
            
            # Save folder data into kdr config
            config = self.adapter.update_config({
                'device_id' : device_id,
                'api_key' : api_key,
                'name' : name,
                'path' : local_path
            })

            return 'Success'
        except IOError as e:
           return e.message

    def acknowledge(self, hostname, devid, remote_folder, local_path):

        """

            Commit the shared remote folder data into local config.xml file
                1. Update the remote_folder path and label
                2. Append the remote_folder to config folders list

            Args:
                remote_folder(folder): syncthing folder object
                local_path: existing local path

        """

        config = self.get_config()

        if self.folder_exists({
            'id' : remote_folder['id']
        }, config):
            # TODO: maybe tell user where they are synchronizing the dev
            raise ValueError('You are already synchronizing this device.')

        remote_folder['path'] = local_path
        remote_folder['label'] = 'sync'
        config['folders'].append(remote_folder)
               
        device = self.find_device(devid, config)
        
        if device:
            device['name'] = hostname
       
        return self.set_config(config)

    def hostname(self):
        return socket.gethostname()
 
    def test(self, arg): 

        print self.completion('/home/jvlarble/Downloads/node-0')
        #print self.scan('/home/jvlarble/Downloads/node-0')
        return

        toks = arg.split('@')
        device_id = toks[0]
        api_key = toks[1]
        host = self.devid_to_ip(device_id)

        print self.get_device_id()
        remote = SyncthingProxy(device_id, host, api_key)
        #print self.sync._interface.options
        print self.get_device_id()
        return

        '''
        print self.sync.sys.status()['myID']
        return
        print self.devid_to_ip( 'UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        print dir(self.sync.sys.set.config)
        print self.sync.misc.device_id(id='UGTMKD2-GTXMPW5-WUSYAVN-HNBHWSD-LT2HXX7-KLKI6AJ-KHY65W2-XX726QD')
        return self.sync.sys.ping()
        '''

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

    def hostname(self, config = None):

        if not config:
            config = self.get_config()

        devices = config['devices']
        
        for d in devices:
            if d['deviceID'] == self.device_id:
                return d['name']

    def request_folder(self, client_hostname, client_devid):
        config = self.get_config()       
        
        self.new_device(
            config = config,
            hostname = client_hostname,
            device_id = client_devid
        )

        config['folders'][0]['devices'].append({
            'deviceID' : client_devid
        })
        
        self.set_config(config)
        self.restart()

        return config

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
