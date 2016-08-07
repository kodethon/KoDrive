from py_syncthing_adapter import Syncthing
import click

# Self-defined
import platform_adapter
from data import custom_errors
from data import syncthing_adt

# Standard library
import os, sys, platform
import time, socket, json
import base64, hashlib, shutil

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
    except Exception as e:
      if self.adapter:
        return self.adapter.get_device_id()
      else:
        return None
        
  def set_config(self, config):
    return self.sync.sys.set.config(config)
    
  def restart(self):
    self.sync.sys.set.restart()

  def stat(self, path):
    if not path[len(path) - 1] == '/':
      path += '/'

    folder = self.find_folder({
      'path' : path
    }) 

    if not folder:
      raise IOError(path + ' is not being synchronized.')
    else:
      return self.sync.db.status(folder=folder['id'])

  def set_rescan_interval(self, secs):
    if type(secs) != int or secs < 0:
      return False

    config = self.get_config()

    for f in config['folders']:
      f['rescanIntervalS'] = secs

    self.set_config(config)
    return True

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

  def completion(self, path, device_num=0):

    if not path[len(path) - 1] == '/':
      path += '/'

    folder = self.find_folder({
      'path' : path
    })
    
    device_id = folder['devices'][device_num]['deviceID']
    max_devices = len(folder['devices']) - 1
    
    # Skip own device
    if device_id == self.get_device_id():
      if device_num >= len(folder['devices']): 
        return {
          'percent' : 100,
          'device_num' : device_num + 1,
          'max_devices' : max_devices
        }
      else:
        device_id = folder['devices'][device_num]['deviceID']

    res = self.sync.db.completion(device=device_id, folder=folder['id'])
    percent = res['completion']
    percent = (device_num  * 100 + percent) / (max_devices * 100) * 100

    if percent == 100:
      device_num += 1

    return {
      'percent' : percent if percent > 0 else 0,
      'device_num' : device_num,
      'max_devices' : max_devices
    } 
  
  def start(self, port=None):    
    path = self.adapter.get_syncthing_path()
    is_new = self.adapter.start_syncthing(path)
    
    # If is new, initialize config file
    if is_new:
      for i in range(0, 10):
        try:
          # The order in which this is done is important!
          # make_client can undo the changes of delete_default_folder
          # if syncthing has not been restart :(
          self.sync = self.adapter.get_gui_hook()
          self.make_client(port)

          st_conf = self.adapter.st_conf_file
          app_conf = self.adapter.app_conf_file
          self.adapter.init_configs(st_conf, app_conf)

          self.adapter.delete_default_folder()
          break
        except Exception as e:
          pass

        time.sleep(0.5)

    return True if self.wait_start(0.5, 10) else False

  def shutdown(self):
    try:
      status = json.loads(self.sync.sys.set.shutdown())
      return status['ok'] == 'shutting down'
    except Exception:
      return False
      
  def ping(self):

    # Run command
    try:
      t = type(self.sync.sys.ping()) 
    except Exception as e:
      return False

    return t == dict
  
  def encode_device_key(self):
    devid = self.get_device_id()
    hostname = self.hostname()
    key = "%s#%s" % (hostname, devid)
    key = key.encode('base64')

    return "".join(key.split())

  def decode_device_key(self, key):
    try:
      key = key.decode('base64')
    except:
     raise custom_errors.InvalidKey(key)

    try:
      toks = key.split('#')
      return {
        'hostname' : toks[0],
        'devid' : toks[1]
      }
    except ValueError: 
      pass

  def encode_key(self, path):
    kdr_config = self.adapter.get_config()
    directories = kdr_config['directories']
    system = kdr_config['system']
  
    # Check if the directory belongs to user
    for key in directories:
      f = directories[key]
      
      if f['local_path']  == path.rstrip('/'):
        if f['is_shared']:
          raise custom_errors.PermissionDenied()
   
    config = self.get_config()
    devid = self.get_device_id()
    if system['server']:
      api_key = config['gui']['apiKey']
      key = "%s@%s@%s" % (devid, path, api_key)
    else:
      folder_config = self.find_folder({
        'path' : path
      }, config)
      folder_id = folder_config['id']
      label = folder_config['label']
      key = "%s#%s#%s#%s" % (devid, self.hostname(), folder_id, label)
    
    key = key.encode('base64')

    return "".join(key.split())
    
  def config_in_sync(self):
    try:
      res = self.sync.sys.insync()
      return res['configInSync']
    except Exception:
      return False

# UTILS
  
  def wait_sync(self, t, intervals, callback=None):
    count = 0 

    while not self.config_in_sync() and count < counters:
      time.sleep(t)
      count += 1

    if count < intervals:
      if callback:
        callback()

      return True
    else:
      return False

  def wait_start(self, t, intervals, **kwargs):
    
    if 'callback' in kwargs:
      callback = kwargs['callback'] 
    else:
      callback = None

    if 'verbose' in kwargs:
      verbose = kwargs['verbose'] 
    else:
      verbose = False

    # Base case
    if intervals <= 0:
      try:
        config = self.get_config()
        return True if config else False
      except Exception:
        return False 

    count = 0
    while not self.ping() and count < intervals:
      time.sleep(t)
      count += 1

      if verbose:
        click.echo("Attempt %i to connect." % count)

    c = True

    try:
      config = self.get_config()

      if not config:
        c = False
    except Exception:
      c = False

    if not c:
      self.wait_start(t, intervals - count, **kwargs)
    else:
      if count < intervals:
        if callback:
          callback()

        return True
      else:
        return False


  def decode_key(self, encoded_key):

    key = "".join(encoded_key.split())
    key = key.decode('base64')

    try:
      key.index("@")
      toks = key.split('@')
      return {
        'devid' : toks[0],
        'remote_path' : toks[1],
        'api_key' : toks[2]
      }
    except ValueError:
      pass

    try:
      key.index("#")
      toks = key.split("#")
      return {
        'devid' : toks[0],
        'hostname' : toks[1],
        'folder_id' : toks[2],
        'label' : toks[3]
      }
    except ValueError:
      pass

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
      'deviceID' : kwargs['device_id'],
      'name' : kwargs['hostname'],
      'compression' : 'metadata',
      'introducer' : False,
      'certName' : '',
      'address' : ['dynamic']
    }
    
    config = kwargs['config']

    if not config['devices']:
      config['devices'] = []
    
    config['devices'].append(record)
              
  def device_exists(self, client_devid, config=None):

    if not config:
      config = self.get_config()       

    return self.find_device(client_devid, config) != None

  def find_device(self, client_devid, config=None):
      
    if not config:
      config = self.get_config()

    for d in config['devices']:
      device_id = self.get_devid(d)
      
      if device_id == client_devid:
        return d

  def delete_device(self, devid, config):
    devices = config['devices']

    for i, d in enumerate(devices):
      device_id = self.get_devid(d)
      
      if device_id == devid:
        del devices[i]
        return True

    return False

  def delete_device_from_folder(self, path, devid, config):
    # list of folders
    folders = config['folders']

    for i, f in enumerate(folders):
      if path.rstrip('/') == f['path'].rstrip('/'):
        for n, d in enumerate(f['devices']):
          device_id = self.get_devid(d)

          if device_id == devid:
            del folders[i]['devices'][n]
            return True

    return False

  def delete_folder(self, path, config):
    # list of folders
    folders = config['folders']
    
    for i, f in enumerate(folders):
      if path.rstrip('/') == f['path'].rstrip('/'):
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

        if k == 'path':
          if object[k].rstrip('/') == f[k].rstrip('/'):
            n += 1
        else: 
          if object[k] == f[k]:
            n += 1

        d += 1

      if n == d:
        return f 

  def device_exists_in_folder(self, path, devid, config=None):

    if not config:
      config = self.get_config()

    folder = self.find_folder({
      'path' : path
    }, config)

    if not folder:
      return False

    for d in folder['devices']:
      device_id = self.get_devid(d)

      if device_id == devid:
        return True

    return False

  def folder_exists(self, object, config = None):
    
    if not config:
      config = self.get_config()

    f = self.find_folder(object, config) 
    return f != None

  def get_devid(self, dev_obj):
    if 'deviceID' in dev_obj:
      return dev_obj['deviceID']
    else:
      return dev_obj['deviceId']

  def to_st_path(self, path):
    if not path[len(path) - 1] == '/':
      path += '/'

    return path

class SyncthingClient(SyncthingFacade):
   
  def __init__(self, adapter):
    SyncthingFacade.__init__(self)
    
    self.adapter = adapter

    try:
      self.sync = self.adapter.get_gui_hook()
    except Exception:
      pass

  def add(self, **kwargs):

    if os.path.isfile(kwargs['path'].rstrip('/')):
      raise custom_errors.NotDirectory(kwargs['path'].rstrip('/'))

    devid = self.get_device_id()
    config = self.get_config()
    folders = config['folders']

    for f in folders:
      if f['path'].rstrip('/') == kwargs['path'].rstrip('/'):
        raise custom_errors.FileExists(kwargs['path'])

    folders.append({
      'rescanIntervalS' : 30,
      'copiers' : 0,
      'pullerPauseS' : 0,
      'autoNormalize' : True,
      'id' : hashlib.sha1(kwargs['path']).hexdigest(),
      'scanProgressIntervalS' : 0,
      'hashers' : 0,
      'pullers' : 0,
      'invalid' : '',
      'label' : kwargs['tag'],
      'minDiskFreePct' : 1,
      'pullerSleepS' : 0,
      'type' : 'readwrite',
      'disableSparseFiles' : False,
      'path' : kwargs['path'],
      'ignoreDelete' : False,
      'ignorePerms' : False,
      'devices' : [{'deviceID' : devid}],
      'disableTempIndexes' : False,
      'maxConflicts' : 10,
      'order' : 'random',
      'versioning' : {'type': '', 'params': {}}
    })
    self.set_config(config)
    self.restart()

    # Save folder data into kdr config
    config = self.adapter.set_dir_config({
      'device_id' : devid,
      'api_key' : hashlib.sha1(devid + kwargs['path']).hexdigest(),
      'label' : kwargs['tag'],
      'local_path' : kwargs['path'],
      'remote_path': '',
      'is_shared' : False
    }) 
    open(os.path.join(kwargs['path'], '.stfolder'), 'w').close()

    return True

  def make_server(self, port=None):
    kdr_config = self.adapter.get_config()
    kdr_config['system']['server'] = True
    self.adapter.set_config(kdr_config)

    syncthing_config = self.get_config()
    config_path = self.adapter.st_conf_file

    if not port:
      address = self.adapter.get_gui_address(config_path)
      port = address.split(':')[1]

    syncthing_config['gui']['address'] = "0.0.0.0:%s" % str(port)

    self.set_config(syncthing_config)
    self.restart()
    self.sync = self.adapter.get_gui_hook()

  def make_client(self, port=None):
    kdr_config = self.adapter.get_config()
    kdr_config['system']['server'] = False
    self.adapter.set_config(kdr_config)

    syncthing_config = self.get_config()
    config_path = self.adapter.st_conf_file

    if not port:
      address = self.adapter.get_gui_address(config_path)
      port = address.split(':')[1]

    syncthing_config['gui']['address'] = "127.0.0.1:%s" % port

    self.set_config(syncthing_config)
    self.restart()
    self.sync = self.adapter.get_gui_hook()

  def link(self, **kwargs):

    """

      1. If config.json not created:
        Create config as ~/.config/kdr/config.json
        Initialize contents in confing.json
      else
        Append new folder data to config
      
      2. Notify the remote device that this machine
         wants to connect to it.

      Args:
        device_id(str): ID to uniquely identify remote device
        api_key(str): key to access remote device API
        local_path(str): path to folder user wants to sync to
        remote_path(str): path to folder user wants to sync from
    
      returns label AKA tag

    """
    
    device_id = kwargs['device_id']
    api_key = kwargs['api_key']
    local_path = kwargs['local_path']
    remote_path = kwargs['remote_path']

    # Check if the device id is valid
    if 'error' in self.sync.misc.device_id(id=device_id):
      raise KeyError('Invalid Key.')

    config = self.get_config()
    
    if self.folder_exists({
      'path' : local_path
    }):
      raise custom_errors.AlreadyAdded()

    #self_devid = self.get_device_id()
    if not self.device_exists(device_id):
      self.new_device(config=config, device_id=device_id)
      self.set_config(config)
      self.restart()
    
    if 'remote_host' in kwargs:
      host = kwargs['remote_host']
    else:
      host = self.devid_to_ip(device_id)

    # Request remote to share its folder with us
    remote = SyncthingProxy(
      device_id, host, api_key, 
      port=kwargs['remote_port'] if 'remote_port' in kwargs else None
    )
    remote.wait_start(0.5, 10)
    remote_config = remote.request_folder(
      self.hostname(),    
      self.get_device_id()
      #self_devid
    )
    
    # Find the remote folder
    if remote_path:
      remote_folder = self.find_folder({
        'path' : remote_path
      }, remote_config)
    else:
      remote_folder = remote_config['folders'][0] 

    label = kwargs['tag'] if 'tag' in kwargs else remote_folder['label']
    global_remote_folder = remote_folder['path']
    
    # Save the folder data into syncthing config

    self.wait_start(0.5, 10) # Wait for the self.restart
    self.acknowledge(
      device_id=device_id,
      api_key = api_key,
      hostname=remote.hostname(remote_config), 
      folder_obj=remote_folder, 
      label=label,
      local_path=local_path,
      remote_path=remote_folder['path'],
      host=remote.host,
      port=remote.port,
      server=True
    )
    return label

  def acknowledge(self, **kwargs):

    """

      Commit the shared remote folder data into local config.xml file
        1. Update the remote_folder path and label
        2. Append the remote_folder to config folders list

      Args:
        remote_folder(folder): syncthing folder object
        local_path: existing local path

    """

    device_id = kwargs['device_id']
    config = self.get_config()

    if 'r_folder_id' in kwargs:
      r_folder_id = kwargs['r_folder_id']
      remote_folder = syncthing_adt.Folder(
        id=r_folder_id,
        label=kwargs['label'],
        path=kwargs['local_path'],
        deviceID=self.get_device_id()
      )
      remote_folder.add_device(device_id)
      remote_folder = remote_folder.obj
    else:
      remote_folder = kwargs['folder_obj']
      remote_folder['path'] = kwargs['local_path']
      r_folder_id = remote_folder['id']
    
    # Check syncthing config to make sure the user is not
    # already synchronizing this folder
    if self.folder_exists({
      'path' : kwargs['local_path']
    }, config):
      # TODO: maybe tell user where they are synchronizing the dev
      raise ValueError('You are already synchronizing this folder.')
    
    # Modify syncthing config
    config['folders'].append(remote_folder)
    config['label'] = kwargs['label']

    self.new_device(config=config, device_id=device_id)
           
    device = self.find_device(device_id, config)
    
    if device:
      device['name'] = kwargs['hostname']

    if 'api_key' in kwargs:
      api_key = kwargs['api_key']
    else:
      api_key = ''

    # Save folder data into kdr config
    self.adapter.set_dir_config({
      'device_id' : device_id,
      'api_key' : api_key,
      'label' : kwargs['label'],
      'local_path' : kwargs['local_path'],
      'remote_path': kwargs['remote_path'] if 'remote_path' in kwargs else '',
      'is_shared' : True,
      'host' : kwargs['host'] if 'host' in kwargs else None,
      'port' : kwargs['port'] if 'port' in kwargs else None,
      'server' : kwargs['server'] if 'server' in kwargs else False
    }) 

    self.set_config(config)
    self.restart()

  def hostname(self):
    return socket.gethostname()

  def free(self, local_path):
    '''
      Stop synchronization of local_path
    '''

    dir_config = self.adapter.get_dir_config(local_path)
    r_device_id = None

    if not dir_config:
      raise custom_errors.FileNotInConfig(local_path)
    
    r_device_id = dir_config['device_id']
         
    # Process local ~~~

    # 1. Syncthing config
    config = self.get_config()
    del_folder = self.delete_folder(local_path, config)

    # Check whether folders are still connected to this device 
    device_exists = False
    
    for f in config['folders']:
      if self.device_exists(r_device_id, f):
        device_exists = True
    
    if not device_exists:
      del_device = self.delete_device(r_device_id, config)
        
    # Done processing st config, commit :)
    self.set_config(config)
    self.restart()

    # 2. App config
    kdr_config = self.adapter.get_config()

    for key in kdr_config['directories']: 
      d = kdr_config['directories'][key]
      if d['local_path'].rstrip('/') == local_path.rstrip('/'):
        del kdr_config['directories'][key]
        break
    
    # Done process app config, commit :)
    self.adapter.set_config(kdr_config)

    # If the folder was shared, remove data from remote 
    if dir_config['is_shared'] and dir_config['server']:
      
      # Process remote ~~~
      r_api_key = dir_config['api_key']
      
      if dir_config['host']:
        host = dir_config['host']
      else:
        host = self.devid_to_ip(r_device_id, False)

      remote = SyncthingProxy(
        r_device_id, host, r_api_key,
        port=dir_config['port'] if 'port' in dir_config else None
      )
      r_config = remote.get_config()
      self_devid = self.get_device_id()

      del_device = remote.delete_device_from_folder(
        dir_config['remote_path'],
        self_devid, 
        r_config
      )
      
      # Check to see if no other folder depends has this device
      device_exists = False

      for f in r_config['folders']:
        if self.device_exists(self_devid, f):
          device_exists = True

      if not device_exists:
        remote.delete_device(self_devid, r_config)

      remote.set_config(r_config)
      remote.restart()

    return True

  def tag(self, path, name):
    '''
      Change name associated with path
    '''

    if not path[len(path) - 1] == '/':
      path += '/'

    config = self.get_config()
    folder = self.find_folder({
      'path' : path
    }, config)

    if not folder:
      raise custom_errors.FileNotInConfig(path)

    old_name = folder['label']
    folder['label'] = name
    
    dir_config = self.adapter.get_dir_config(path)
    dir_config['label'] = name
    self.adapter.set_dir_config(dir_config)

    self.set_config(config)
    self.restart

    return old_name
  
  def ls(self): 

    metadata = [
      {'Tag' : [],},
      {'Path' : []}
    ]

    config = self.adapter.get_config()

    if not config:
      return None

    dirs = config['directories']

    # For each directory 
    for key, value in dirs.iteritems(): 

      if value['label']:
        metadata[0]['Tag'].append(value['label'])

      else:
        syncthing_config = self.get_config()
        folders = syncthing_config['folders']

        for f in folders:
          if value['local_path'] + '/' == f['path']:
            value['label'] = f['label']
            metadata[0]['Tag'].append(f['label'])
      # Edge case: fails if label is None, get label from syncthing_config

      metadata[1]['Path'].append(value['local_path'])

    return metadata

  def rename(self, source, target):
    source = ''.join(source)

    if not os.path.exists(source):
      raise custom_errors.NoFileOrDirectory(source, target)

    source_path = os.path.abspath(source)
    target_path = os.path.abspath(target)
    syncthing_config = self.get_config()

    folders = syncthing_config['folders']
    old_key = self.adapter.get_dir_id(source_path)
    new_key = self.adapter.get_dir_id(target_path)
    found = False
    path = None

    # Modify config.xml
    for f in folders:
      if source_path == os.path.abspath(f['path']):

        f['id'] = new_key

        path = source_path[:-len(source)]
        f['path'] = os.path.join(path, target)

        if not f['path'][len(f['path']) - 1] == '/':
          f['path'] += '/'

        self.set_config(syncthing_config)
        found = True
        break

    if not found and os.path.exists(source_path):
      raise custom_errors.FileNotInConfig(source_path)
      # if not found but exists

    #Modify config.json
    kdr_config = self.adapter.get_config()
    
    try:
      kdr_config['directories'][new_key] = kdr_config['directories'][old_key]
      del kdr_config['directories'][old_key]
    except:
      raise custom_errors.InvalidKey(old_key)
      
    if kdr_config['directories'][new_key]['local_path'] == source_path:

      kdr_config['directories'][new_key]['local_path'] = target_path
      shutil.move(source_path, os.path.join(path, target))
      shutil.rmtree(source_path, ignore_errors=True)
      # renames directories in client's local environment

      self.adapter.set_config(kdr_config)
    
    self.restart()
    return

  def move(self, source, target):
    target_path = os.path.abspath(target)
    syncthing_config = self.get_config()
    folders = syncthing_config['folders']
    kdr_config = self.adapter.get_config()
    found = False

    # Modify config.xml
    for item in source:
      item_path = os.path.abspath(item)
      item_path.rstrip('/')
      found = False

      for f in folders:
        if f['path'] == item_path + '/':

          old_key = self.adapter.get_dir_id(item_path)
          reduced_item = item.rstrip('/')
          reduced_item = os.path.basename(reduced_item)
          final_path = os.path.join(target_path, reduced_item)
          f['path'] = final_path

          new_key = self.adapter.get_dir_id(final_path)
          f['id'] = new_key

          if not f['path'][len(f['path']) - 1] == '/':
            f['path'] += '/'

          self.set_config(syncthing_config)

          # Modify config.json
          try:
            kdr_config['directories'][new_key] = kdr_config['directories'][old_key]
            del kdr_config['directories'][old_key]
          except:
            raise custom_errors.InvalidKey(old_key)

          if kdr_config['directories'][new_key]['local_path'] == item_path:
            kdr_config['directories'][new_key]['local_path'] = final_path
            self.adapter.set_config(kdr_config)

          found = True
          break

      shutil.move(item_path, final_path)
      # move into target

    self.restart()
    return

  def mv_edge_case(self, source, target):
    os.remove(target)
    os.rename(''.join(source), target)
    return

  def valid_device_id(self, device_id):
    if len(device_id) != 63:
      return False

    if device_id.count('-') != 7:
      return False

    parts = device_id.split('-')

    for part in parts:
      if len(part) != 7:
        return False

    return True

  def auth(self, key, path):

    try:
      if key == self.encode_device_key():
        raise custom_errors.AuthYourself()
    except:
      try:
        alive = self.handler.ping()
      except:
        alive = False

      if not alive:
        raise custom_errors.CannotConnect()

    self.wait_start(0.5, 10)
    path = os.path.abspath(path)
    kdr_config = self.adapter.get_config()
    directories = kdr_config['directories']
    config = self.get_config()
    devices = config['devices']
    folders = config['folders']

    if not path[len(path) - 1] == '/':
      path += '/'

    if not self.folder_exists({
      'path' : path
    }, config):
      raise custom_errors.FileNotInConfig(path)
    # to check if user did 'kdr add <PATH>'

    for k in directories:
      f = directories[k]

      if f['local_path']  == path.rstrip('/'):
        if f['is_shared']:
          raise custom_errors.PermissionDenied()

    decoded = self.decode_device_key(key)

    if not decoded:
      raise custom_errors.InvalidKey(key)

    device_id = decoded['devid']
    name = decoded['hostname']

    if not self.valid_device_id(device_id):
      raise custom_errors.InvalidKey(key)

    client_devid = {
      u'deviceID' : device_id
    }

    for f in folders:
      if f['path'] == path:

        if client_devid not in f['devices']:
          f['devices'].append(client_devid)

        else:
          raise custom_errors.AuthAlready(name)
        break
    # add devid to folder if not already there

    if not self.device_exists(key):
      try:
        self.new_device(config=config, device_id=device_id, hostname=name)
      except:
        raise custom_errors.DeviceNotFound(key)
      # add device to devices

    self.set_config(config)
    self.restart()
      
    return

  def deauth(self, key, path):

    try:
      if key == self.encode_device_key():
        raise custom_errors.AuthYourself()
    except:
      try:
        alive = self.handler.ping()
      except:
        alive = False

      if not alive:
        raise custom_errors.CannotConnect()

    self.wait_start(0.5, 10)
    path = os.path.abspath(path)
    kdr_config = self.adapter.get_config()
    directories = kdr_config['directories']
    config = self.get_config()
    devices = config['devices']
    folders = config['folders']

    if not path[len(path) - 1] == '/':
      path += '/'

    if not self.folder_exists({
      'path' : path
    }, config):
      raise custom_errors.FileNotInConfig(path)
    # to check if user did 'kdr add <PATH>'

    for k in directories:
      f = directories[k]
      
      if f['local_path']  == path.rstrip('/'):
        if f['is_shared']:
          raise custom_errors.PermissionDenied()

    decoded = self.decode_device_key(key)

    if not decoded:
      raise custom_errors.InvalidKey(key)

    device_id = decoded['devid']
    name = decoded['hostname']

    if not self.valid_device_id(device_id):
      raise custom_errors.InvalidKey(key)

    r_devid = {
      u'deviceID' : device_id
    }

    for f in folders:
      if f['path'] == path:

        if r_devid in f['devices']:
          f['devices'].remove(r_devid)

        else:
          raise custom_errors.AuthAlready(name)

        break
    # remove devid from folder if there

    in_other_folders = False

    for f in folders:
      if r_devid in f['devices'] and path != f['path']:
        in_other_folders = True
        break

    if self.device_exists(device_id) and not in_other_folders:
      try:
        self.delete_device(devid=device_id, config=config)
      except:
        raise custom_errors.DeviceNotFound(key)
    # remove device to devices if device isn't syncing with other folders
    
    self.set_config(config)
    self.restart()
    
    return

    return

  def auth_ls(self):

    self.wait_start(0.5, 10)
    kdr_config = self.adapter.get_config()
    directories = kdr_config['directories']
    config = self.get_config()
    devices = config['devices']
    folders = config['folders']
    body = str()

    for f in folders:
      shared = False  
        
      for k, v in directories.iteritems():
        if f['path'] ==  v['local_path']:
          shared = v['is_shared']
      # if not your folder, don't display

      if len(f['devices']) > 1 and not shared:
        body += f['path']

        for i, val in enumerate(f['devices']):

          if not val['deviceID'] == self.get_device_id():

            r_devid = self.find_device(val['deviceID'], config)

            if not r_devid:
              raise custom_errors.DeviceNotFound(val['deviceID'])

            key = "%s#%s" % (r_devid['name'], val['deviceID'])
            key = key.encode('base64')
            key = "".join(key.split())

            body += '\n\t' + key
      
          if i == len(f['devices']) - 1:
            body += '\n'

        body += '\n'

    if body.endswith('\n'):
      body = body[:-2]

    return body

  def test(self, arg): 
    self.restart()

class SyncthingProxy(SyncthingFacade):

  port = 8384

  def __init__(self, device_id, host, api_key, **kwargs):
    SyncthingFacade.__init__(self)
    
    if not host:
      host = '0.0.0.0' 

    if 'port' in kwargs and kwargs['port']:
      self.port = kwargs['port']   
    
    self.device_id = device_id
    self.host = host
    self.api_key = api_key

    self.sync = Syncthing(
      api_key=api_key, 
      host=host,
      port=self.port
    )

    # If remote host can't be detected, throw a tantrum >:/
    if not self.ping():
      raise IOError('Could not connect to %s:%s.' % (host, self.port))

  def hostname(self, config = None):

    if not config:
      config = self.get_config()

    devices = config['devices']
    
    for d in devices:
      if 'deviceId' in d:
        device_id = d['deviceId']
      else:
        device_id = d['deviceID']

      if device_id == self.device_id:
        return d['name']

  def request_folder(self, client_hostname, client_devid):
    '''
    print 'ARGS -------------------------------------'
    print client_hostname
    print client_devid
    print self.get_device_id()
    '''

    config = self.get_config()       

    self.new_device(
      config = config,
      hostname = client_hostname,
      device_id = client_devid
    )
    
    folder = config['folders'][0]

    if not folder['devices']:
      folder['devices'] = []
    
    folder['devices'].append({
      'deviceID' : client_devid
    })

    self.set_config(config)
    self.restart()

    return config

  def disconnect(self):
    return


def get_handler(home=None):
  
  system = platform.system()

  if system == "Linux":
    return SyncthingClient(
      platform_adapter.SyncthingLinux64(home)
    ) # Linux
  elif system == "Darwin":
    return SyncthingClient(
      platform_adapter.SyncthingMac64(home)
    ) # MacOSX
  elif system == "Windows":
    return SyncthingClient(
      platform_adapter.SyncthingWin64()
    ) # TODO: Windows

  raise Exception("%s is not currently supported." % system)

