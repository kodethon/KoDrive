from py_syncthing_adapter import Syncthing

# Self-defined
import platform_adapter
import custom_errors

# Standard library
import sys, platform, time
import socket, json, base64
import os

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
      count = 1
      host = None

      # Wait for changes to take effect
      while count <= 10:

        host = self.devid_to_ip(devid, False)           

        if not host:
          print "Attempt %i to discover device." % count
          time.sleep(1)
          count += 1
        else:
          if count > 1:
            print 'Device successfully discovered!'
          
          return host

      return None

  def new_device(self, **kwargs):

    if not 'hostname' in kwargs: 
      kwargs['hostname'] = 'Unknown'

    record = {
      'deviceId' : kwargs['device_id'],
      'name' : kwargs['hostname'],
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

  def delete_device(self, devid, config):
    devices = config['devices']

    for i, d in enumerate(devices):
      device_id = d['deviceID']
      
      if device_id == devid:
        del devices[i]
        return True

    return False

  def delete_device_from_folder(self, path, devid, config):
    if not path[len(path) - 1] == '/':
      path += '/'

    # list of folders
    folders = config['folders']
		
    for i, f in enumerate(folders):
      if path == f['path']:
        for n, d in enumerate(f['devices']):
          if d['deviceID'] == devid:
            del folders[i]['devices'][n]
            return True

    return False

  def delete_folder(self, path, config):

    if not path[len(path) - 1] == '/':
      path += '/'

    # list of folders
    folders = config['folders']
		
    for i, f in enumerate(folders):
      if path == f['path']:
        del folders[i]
        return True

    return False

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
   
  global_name = None
  global_remote_folder = None  

  def __init__(self, adapter):
    SyncthingFacade.__init__(self)

    self.adapter = adapter

    try:
      self.sync = self.adapter.get_gui_hook()
    except Exception:
      pass

  def link(self, key, name, local_path):

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
    
    global_name = name

    try:
      toks = key.split('@')
      device_id = toks[0]
      api_key = toks[1]
    except IndexError as e:
      raise KeyError('Invalid Key.')

    # Check if the device id is valid
    if 'error' in self.sync.misc.device_id(id=device_id):
      raise KeyError('Invalid Key.')

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
    # *** Should be more dynamic in the future
    remote_folder = remote_config['folders'][0] 
    name = name or remote_folder['label']
    global_remote_folder = remote_folder['path']

    # Save folder data into kdr config
    config = self.adapter.update_config({
      'device_id' : device_id,
      'api_key' : api_key,
      'label' : name,
      'local_path' : local_path,
      'remote_path': remote_folder['path'] 
    }) 

    # Save the folder data into syncthing config
    self.acknowledge(
      hostname=remote.hostname(remote_config), 
      devid=device_id,
      folder_obj=remote_folder, 
      tag=name,
      local_path=local_path
    )

    self.restart()

    return name

  def acknowledge(self, **kwargs):

    """

      Commit the shared remote folder data into local config.xml file
        1. Update the remote_folder path and label
        2. Append the remote_folder to config folders list

      Args:
        remote_folder(folder): syncthing folder object
        local_path: existing local path

    """

    config = self.get_config()
    remote_folder = kwargs['folder_obj']

    if self.folder_exists({
      'id' : remote_folder['id']
    }, config):
      # TODO: maybe tell user where they are synchronizing the dev
      raise ValueError('You are already synchronizing this device.')

    remote_folder['path'] = kwargs['local_path']
    config['folders'].append(remote_folder)
    if kwargs['tag']:
      config['lablel'] = kwargs['tag']
           
    device = self.find_device(kwargs['devid'], config)
    
    if device:
      device['name'] = kwargs['hostname']
   
    return self.set_config(config)

  def hostname(self):
    return socket.gethostname()

  def unlink(self, local_path):

    # Process remote
    dir_config = self.adapter.get_dir_config(local_path)

    if not dir_config:
      raise custom_errors.FileNotInConfig(local_path)
    
    r_api_key = dir_config['api_key']
    r_device_id = dir_config['device_id']
    host = self.devid_to_ip(r_device_id, False)
    
    remote = SyncthingProxy(r_device_id, host, r_api_key)
    r_config = remote.get_config()

    del_device = remote.delete_device_from_folder(
      dir_config['remote_path'],
      self.get_device_id(), 
      r_config
    )

    if not del_device:
      raise custom_errors.DeviceNotFoundError(remote.hostname())
      
    config = self.get_config()
    del_folder = self.delete_folder(local_path, config)

    if not del_folder:
      raise custom_errors.FileNotInConfig(local_path)

    del_device = self.delete_device(r_device_id, config)

    if not del_device:
      raise DeviceNotFoundError(remote.hostname())
    
    # All good, commit
    remote.set_config(r_config)
    self.set_config(config)
    remote.restart()
    self.restart()

    return True


  def rename(self, source, target):
    source_path = os.path.abspath(source)
    config = self.get_config()

    folders = config['folders']
    found = False

    for f in folders:
      if source_path == os.path.abspath(f['path']):

        path = source_path[:-len(source)]
        f['path'] = os.path.join(path, target)

        if not f['path'][len(f['path']) - 1] == '/':
          f['path'] += '/'

        self.adapter.update_config({
          'device_id' : self.get_device_id(),
          'api_key' : config['gui']['apiKey'],
          'label' : self.global_name,
          'local_path' : f['path'],
          'remote_path': self.global_remote_folder
        }) 

        found = True
        break

    if not found:
      raise ValueError('fatal: renaming %s failed: No such directory' % os.path.abspath(source))

    os.rename(os.path.join(path, source), os.path.join(path, target))
    # renames directories in client's local environment

    # TODO: remote directory

    # remote.set_config(r_config)
    self.set_config(config)
    # remote.restart()
    self.restart()

    return

  def test(self, arg): 
  
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

    if not host:
      raise IOError('Could not find remote host.')
    
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

