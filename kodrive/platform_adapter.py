import click 
from .py_syncthing_adapter import Syncthing 

from .data import custom_errors 
from .data import mac_plist_adt
from .data import autostart as aust

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

import os, subprocess, socket
import json, hashlib, plistlib
import urllib, copy, errno

class PlatformBase(object):

  app_config = 'config.json'
  st_config = 'config.xml'
  st_binary = 'syncthing'
  st_inotify_binary = 'syncthing-inotify'
  stfolder = '.stfolder'
  st_version = '0.14.7'
  dl_server = 'http://cumulus.cs.ucdavis.edu'

  # Specifies whether to update kodrive config
  migrate = True
  default_config = {
    'directories' : {},
    'system' : {
      'server' : False,
      'sync-speed' : 0
    }
  }
  
  def platform_get_api_key(self, config_path):
    tree = ET.parse(config_path)
    return tree.find('gui').find('apikey').text
    
  def platform_get_folders(self, config_path):
  	tree = ET.parse(config_path)
  	folders = []
  	
  	for f in tree.findall('folder'):
  		folders.append(f.attrib)
  		
  	return folders

  def platform_find_folder(self, config_path, folder_path):
    tree = ET.parse(config_path)
    for f in tree.findall('folder'):
      
      path = f.attrib['path']
      if path == folder_path:
      	devices = []
      	for d in f.findall('device'):
      		devices.append(d.attrib)
      		
      	folder = f.attrib
      	folder['devices'] = devices
	
        return folder

  def platform_set_folder(self, config_path, folder):
    tree = ET.parse(config_path)
    for f in tree.findall('folder'):
      
      path = f.attrib['path']
      if path == folder['path']:

      	for d in f.findall('device'):
      		f.remove(d)

      	for d in folder['devices']:
      		device = Element('device')
      		device.text=' '
      		device.set('id', d['id'])
      		f.insert(0, device)

    tree.write(config_path)

  def get_gui_address(self, config_path):   
    tree = ET.parse(config_path)
    return tree.find('gui').find('address').text

  def set_gui_address(self, config_path, address):
    tree = ET.parse(config_path)
    tree.find('gui').find('address').text = str(address)
    tree.write(config_path)
  
  def get_listen_address(self, config_path):
    tree = ET.parse(config_path)
    addresses = tree.find('options').findall('listenAddress')
    return addresses[len(addresses) - 1].text
    
  def set_listen_address(self, config_path, address):
    tree = ET.parse(config_path)
    addresses = tree.find('options').findall('listenAddress') 
    addresses[len(addresses) - 1].text = str(address)
    tree.write(config_path)

  def init_configs(self, st_conf, app_conf, **kwargs):
    
    tree = ET.parse(st_conf)
    options = tree.find('options')

    # Set syncthing options
    options.find('relayReconnectIntervalM').text = '1'
    options.find('reconnectionIntervalS').text = '30' if kwargs['server'] else '5'
    options.find('overwriteRemoteDeviceNamesOnConnect').text = 'false' if kwargs['server'] else 'true'
    options.find('localAnnounceEnabled').text = 'true' if kwargs['lcast'] else 'false'
    tree.write(st_conf)
    
    # Save device id to kodrive config
    if 'is_new' in kwargs:
      devid = tree.find('device').get('id')
      kodrive_config = self.get_platform_config(app_conf)
      kodrive_config['system']['devid'] = devid
      self.set_platform_config(app_conf, kodrive_config)

  def start_platform_syncthing(self, folder_path, **kwargs):
    st_conf_dir = kwargs['st_conf_dir']
    st_conf_file = kwargs['st_conf_file']

    command = os.path.join(folder_path, self.st_binary)
    log_path = os.path.join(st_conf_dir, 'log')
    opts = [
        command, '-no-browser', '-logfile', log_path, 
        '-home', os.path.join(st_conf_dir)
    ]
    
    # Check if this is first time starting syncthing
    new_flag = False

    if not os.path.exists(st_conf_file):
      new_flag = True
    else:
      gui_address = self.get_gui_address(st_conf_file)
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      toks = gui_address.split(':')
      host = toks[0]
      port = int(toks[1])
        
      # Check if port is available, if it isn't try another port
      p = self.get_available_port(host, port) 
      
      if p != port:
        gui_address = host + ':' + str(p)
        self.set_gui_address(st_conf_file, gui_address)
      
      # Check listen address port is available  
      listen_address = self.get_listen_address(st_conf_file)
      toks = listen_address.split(':')
      
      port = int(toks[2]) if len(toks) == 3 else None
      p = self.get_available_port(host, port)

      if p != port:
        listen_address = ':'.join(['tcp://' + host, str(p)])
        self.set_listen_address(st_conf_file, listen_address)
        
    #opts.append('-gui-address')
    #opts.append(gui_address)
    
    # Check if a migration is needed
    if self.migrate:
      self.migrate_config()
    
    # Set env variable to disable upgrades
    os.environ['HOME'] = os.path.expanduser('~')
    os.environ['STNOUPGRADE'] = '1'
    DEVNULL = open(os.devnull, 'w') 
    process = subprocess.Popen(opts, stdout=DEVNULL)
    
    # Enable inotify if prompted
    command = os.path.join(folder_path, self.st_inotify_binary)
    if 'inotify' in kwargs and kwargs['inotify']:
      # Append output to log
      log = open(log_path, 'a')
      process = subprocess.Popen([command], stderr=log, stdout=log)

    return new_flag

  def set_platform_dir_config(self, folder_path, object):

    config_path = os.path.join(folder_path, self.app_config) 

    # If config file does not exist, create it
    # And then add the new directory data into it
    if not os.path.exists(config_path):
      
      if not os.path.exists(folder_path):
        os.makedirs(folder_path)

      metadata = self.create_dir_metadata(object)
      record = self.create_dir_record(object, metadata)

      self.create_config(config_path, directories=record) 
    else:
      self.append_dir_metadata(config_path, object)

  def get_platform_config(self, config_path):
    try:
      with open(config_path, "r") as f:
        raw = f.read()
        return json.loads(raw)
    except Exception as e:
      return None

  def set_platform_config(self, config_path, raw):
    with open(config_path, "w") as f:
      f.write(json.dumps(raw))

  def get_platform_dir_config(self, config_path, local_path):
    config = self.get_platform_config(config_path)

    if not config:
      return None
      
    else:
      dir_id = self.get_dir_id(local_path)

      try:
        return config['directories'][dir_id]
      except:
        custom_errors.FileNotInConfig(local_path)

  def get_platform_gui_hook(self, config_path):
    tree = ET.parse(config_path)
    api_key = tree.find('gui').find('apikey').text
    address = tree.find('gui').find('address').text
    toks = address.split(':')
    host = toks[0]
    port = toks[1]

    return Syncthing(api_key=api_key, port=int(port), host=host)

  def get_platform_device_id(self, config_path):
    kodrive_config = self.get_platform_config(config_path)
    sys_config = kodrive_config['system']
    return sys_config['devid'] if 'devid' in sys_config else None
  
  def create_config(self, config_path, **kwargs):
    
    conf_dir = os.path.dirname(config_path)
    if not os.path.exists(conf_dir):
      os.makedirs(conf_dir)
    
    config = copy.deepcopy(self.default_config)

    for key in kwargs:
      config[key] = kwargs[key]

    fp = open(config_path, 'w')
    fp.write(json.dumps(config))
    fp.close

    # What happens if write fails?

    return config

  def create_dir_metadata(self, object):
    device_id = object['device_id']

    return {
      'device_id' : device_id,
      'api_key' : object['api_key'],
      'local_path' : object['local_path'],
      'remote_path' : object['remote_path'] if 'remote_path' in object else '',
      'host' : object['host'] if 'host' in object else '',
      'port' : object['port'] if 'port' in object else '',
      
      # Tag provided by user to identify the dir
      'label' : object['label'],

      # Denotes whether the dir belongs to the user or 
      # was linked from a remote device
      'is_shared' : object['is_shared'],

      # Denotes whether the dir was from a 
      # device running in client or server mode
      'server' : object['server'] if 'server' in object else False
    }

  def create_dir_record(self, object, metadata):
    
    name = self.get_dir_id(object['local_path'])
    return {name : metadata}

  def append_dir_metadata(self, config_path, object):

    metadata = self.create_dir_metadata(object)
    record = self.create_dir_record(object, metadata)

    with open(config_path, "r+") as f:
      raw = f.read()
      f.seek(0)
        
      if len(raw) > 0:

        try:
            config = json.loads(raw)
        except Exception as e:
            raise IOError("Corrupted config.json file in %s" % folder_path)

        name = self.get_dir_id(object['local_path'])
        config['directories'][name] = metadata

        f.write(json.dumps(config))
        f.truncate()
        
        # TODO: Should handle corrupt config files later

      else:
        config = self.create_config(folder_path, directories=record)

  def get_dir_id(self, local_path):
    local_path = local_path.rstrip('/')
    return hashlib.sha1(local_path).hexdigest()

  def delete_platform_folder(self, **kwargs):
    folder_path = kwargs['folder_path']
    config_path = kwargs['config_path'] 
    files = os.listdir(folder_path)
    deleted = False

    if 'force' in kwargs or (len(files) == 1 and files[0] == self.stfolder):
      os.remove(os.path.join(folder_path, self.stfolder))
      os.rmdir(folder_path)
      deleted = True
      
    if deleted or 'force' in kwargs or 'force_config' in kwargs:
      # Update syncthing config to reflect changes
      if os.path.exists(config_path):
        tree = ET.parse(config_path)
        folders = tree.findall('folder')
        for folder in folders:
          attrs = folder.attrib
          if attrs['path'].rstrip('/') == folder_path.rstrip('/'):
            root = tree.getroot()
            root.remove(folder)
            tree.write(config_path)

            return tree
  
  # Creates a .kodrive folder 
  def broadcast_folder_info(self, folder_path, **kwargs):
  	dir_path = os.path.join(folder_path, '.kodrive')

  	if not os.path.exists(dir_path):
  		os.makedirs(dir_path)
  		
  	conf_path = os.path.join(dir_path, 'config.json')
  	
  	if os.path.exists(conf_path):
			fp = open(conf_path, 'r+')
			config = json.loads(fp.read())
			config['devices'] = kwargs['devices']

			fp.write(json.dumps(config))
  	else:
			config = {}
			if 'devices' in kwargs: 
				config['devices'] = kwargs['devices']
			
			# Create config.json
			with open(conf_path, 'w') as f:
				f.write(json.dumps(config))
	
	# Utility to find an available port
  def get_available_port(self, host='0.0.0.0', port=1025):
    if not port:
      port= 1025

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if sock.connect_ex((host, port)) == 0:
        port += 1
        # Continue incrementing until an open port is found
        while port < 65535 and sock.connect_ex((host, port)) == 0:
          port += 1

    return port

### Linux Adapter
class SyncthingLinux64(PlatformBase): 
  
  rel_st_conf_dir = '.config/syncthing'
  rel_app_conf_dir  = '.config/kodrive'
  
  def __init__(self, home=None):
    if home:
      self.home_dir = home
    else:
      self.home_dir = os.path.expanduser('~')

    self.app_conf_dir = os.path.join(self.home_dir, self.rel_app_conf_dir)
    self.app_conf_file = os.path.join(self.app_conf_dir, self.app_config)

    self.st_conf_dir = os.path.join(self.home_dir, self.rel_st_conf_dir)
    self.st_conf_file = os.path.join(self.st_conf_dir, self.st_config)
    
    if not os.path.exists(self.app_conf_file):
      self.create_config(self.app_conf_file)
    else:
      # Ensure that all the sections are up to date
      config = self.get_platform_config(self.app_conf_file)

      if not config or len(config) == 0:
        self.create_config(self.app_conf_file)
      else:
        updated = False

        for key in self.default_config:
          if key not in config:
            config[key] = self.default_config[key]
            updated = True
        
        if updated:
          self.set_platform_config(self.app_conf_file, config)

  @property
  def config_path(self):
    return self.app_conf_file
    
  def get_folders(self):
  	return self.platform_get_folders(self.st_conf_file)

  def find_folder(self, path):
    if path[len(path) - 1] != '/':
      path += '/'

    return self.platform_find_folder(self.st_conf_file, path)

  def folder_exists(self, path):
    if path[len(path) - 1] != '/':
      path += '/'

    return self.platform_find_folder(self.st_conf_file, path) != None

  def get_api_key(self):
    return self.platform_get_api_key(self.st_conf_file)

  def get_config(self):
    return self.get_platform_config(self.app_conf_file)

  def set_config(self, config):
    return self.set_platform_config(self.app_conf_file, config)

  def set_folder(self, folder):
  	return self.platform_set_folder(self.st_conf_file, folder)

  def get_dir_config(self, local_path):
    '''
      Return dir object specified by local path from config.json
    '''
    return self.get_platform_dir_config(self.app_conf_file, local_path)

  def set_dir_config(self, object):
    self.set_platform_dir_config(self.app_conf_dir, object)

  # Syncthing methods
  def get_gui_hook(self):
    return self.get_platform_gui_hook(self.st_conf_file)

  def get_device_id(self):
    return self.get_platform_device_id(self.app_conf_file)

  def get_syncthing_path(self):
    
    linux_64_bit_file = "syncthing-linux-amd64-v%s" % self.st_version
    syncthing_path = os.path.join('/var/opt', linux_64_bit_file)

    if os.path.exists(syncthing_path):
      return syncthing_path

    dest = os.path.join(self.home_dir, '.st')

    if not os.path.exists(dest):
      os.makedirs(dest) 

    syncthing_path = os.path.join(dest, linux_64_bit_file)

    # If syncthing doesn't exist, install it
    if not os.path.exists(syncthing_path):

      #linux_64_bit_repo = "https://github.com/syncthing/syncthing/releases/download/v%s" % self.st_version
      linux_64_bit_tar = "syncthing-linux-amd64-v%s.tar.gz" % self.st_version
      linux_64_bit_repo = os.path.join(self.dl_server, 'kodrive')
      dest_tmp = os.path.join('/tmp', linux_64_bit_tar)
      
      if not os.path.exists(os.path.join(dest_tmp, linux_64_bit_tar)):
        urllib.urlretrieve(os.path.join(linux_64_bit_repo, linux_64_bit_tar), dest_tmp)

      src = dest_tmp
      command = "tar -zxvf %s --directory %s" % (src, dest)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    return syncthing_path

  def start_syncthing(self, folder_path, **kwargs):   
    kwargs['st_conf_dir'] = self.st_conf_dir
    kwargs['st_conf_file'] = self.st_conf_file

    return self.start_platform_syncthing(folder_path, **kwargs)

  def migrate_config(self):
    # Note: only migrates 2 layers down
    kodrive_config = self.get_config()
    for i in kodrive_config:
      if not type(kodrive_config[i]) == object:
        self.default_config[i] = kodrive_config[i]
      else:
        for j in kodrive_config[i]:
          self.default_config[i][j] = kodrive_config[i][j]

    self.set_config(self.default_config)

  def delete_default_folder(self):
    home_dir = os.path.expanduser('~')
    sync_folder = os.path.join(home_dir, 'Sync')
    self.delete_platform_folder(
      folder_path=sync_folder, 
      config_path=self.st_conf_file,
      force_config=True
    )

  def autostart(self, folder_path):
    home = os.path.expanduser('~')
    dirpath = os.path.join(home, '.config', 'systemd', 'user')
    
    # Creates folder if it doesn't exist
    if not os.path.exists(dirpath):
      os.makedirs(dirpath)
    
    service_name = 'syncthing.service'
    st_service_path = os.path.join(dirpath, service_name)
    
    if not os.path.exists(st_service_path):
      with open(st_service_path, "w") as f:
        f.write(aust.getSyncthingService())

    # Enable autostart (some platforms may not support systemd)
    try:
      opts = [
        'systemctl', '--user', 'enable', st_service_path
      ]
      DEVNULL = open(os.devnull, 'w') 
      process = subprocess.Popen(opts, stdout=DEVNULL)

      opts = [
        'systemctl', '--user', 'start', st_service_path 
      ]
      process = subprocess.Popen(opts, stdout=DEVNULL)
    except Exception as e:
      pass 

  # Not used, kept for reference
  def disable_autostart(self):
    return

### Mac Adapter
class SyncthingMac64(PlatformBase): 

  rel_st_conf_dir = 'Library/Application Support/Syncthing'
  rel_app_conf_dir  = '.config/kodrive'

  def __init__(self, home=None):
    if home:
      self.home_dir = home
    else:
      self.home_dir = os.path.expanduser('~')

    self.app_conf_dir = os.path.join(self.home_dir, self.rel_app_conf_dir)
    self.app_conf_file = os.path.join(self.app_conf_dir, self.app_config)

    self.st_conf_dir = os.path.join(self.home_dir, self.rel_st_conf_dir)
    self.st_conf_file = os.path.join(self.st_conf_dir, self.st_config)
    
    if not os.path.exists(self.app_conf_file):
      self.create_config(self.app_conf_file)
    else:
      # Ensure that all the sections are up to date
      config = self.get_platform_config(self.app_conf_file)

      if not config or len(config) == 0:
        self.create_config(self.app_conf_file)
      else:
        updated = False

        for key in self.default_config:
          if key not in config:
            config[key] = self.default_config[key]
            updated = True
        
        if updated:
          self.set_platform_config(self.app_conf_file, config)

  @property
  def config_path(self):
    return self.app_conf_file
    
  def get_folders(self):
  	return self.platform_get_folders(self.st_conf_file)

  def find_folder(self, path):
    if path[len(path) - 1] != '/':
      path += '/'

    return self.platform_find_folder(self.st_conf_file, path)

  def folder_exists(self, path):
    if path[len(path) - 1] != '/':
      path += '/'

    return self.platform_find_folder(self.st_conf_file, path) != None

  def get_api_key(self):
    return self.platform_get_api_key(self.st_conf_file)

  def get_config(self):
    return self.get_platform_config(self.app_conf_file)

  def set_config(self, config):
    return self.set_platform_config(self.app_conf_file, config)

  def get_dir_config(self, local_path):
    '''
      Return dir object specified by local path from config.json
    '''
    return self.get_platform_dir_config(self.app_conf_file, local_path)

  def set_dir_config(self, object):
    self.set_platform_dir_config(self.app_conf_dir, object)

  # Syncthing methods
  def get_gui_hook(self):
    return self.get_platform_gui_hook(self.st_conf_file)

  def get_device_id(self):
    return self.get_platform_device_id(self.app_conf_file)

  def get_syncthing_path(self):
    
    dest = os.path.join(self.home_dir, '.st')

    if not os.path.exists(dest):
      os.makedirs(dest) 

    mac_64_bit_file = "syncthing-macosx-amd64-v%s" % self.st_version
    syncthing_path = os.path.join(dest, mac_64_bit_file)
    
    # If syncthing doesn't exist, install it
    if not os.path.exists(syncthing_path):
      dest_tmp = '/tmp'

      # mac_64_bit_repo = "https://github.com/syncthing/syncthing/releases/download/v%s" % self.st_version
      mac_64_bit_tar = "syncthing-macosx-amd64-v%s.tar.gz" % self.st_version
      mac_64_bit_repo = "http://cumulus.cs.ucdavis.edu/kodrive/"
      
      if not os.path.exists(os.path.join(dest_tmp, mac_64_bit_tar)):
        link = mac_64_bit_repo + '/' + mac_64_bit_tar
        urllib.urlretrieve(link, os.path.join(dest_tmp, mac_64_bit_tar))

      src = dest_tmp
      command = "tar -zxvf %s/%s --directory %s" % (src, mac_64_bit_tar, dest)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    return syncthing_path

  def start_syncthing(self, folder_path, **kwargs):   
    
    new_flag = False

    command = os.path.join(folder_path, self.st_binary)
    log_path = os.path.join(self.st_conf_dir, 'log')
    opts = [
      command, '-no-browser', '-logfile', log_path, 
      '-home', os.path.join(self.st_conf_dir)
    ]

    if not os.path.exists(self.st_conf_file):
      new_flag = True
    else:  
      gui_address = self.get_gui_address(self.st_conf_file)
      toks = gui_address.split(':')
      host = toks[0]
      port = int(toks[1])
      
      p = self.get_available_port(host, port)
      
      if p != port:
        gui_address = host + ':' + str(p)
        self.set_gui_address(self.st_conf_file, gui_address)
        
      # Check listen address port is available  
      listen_address = self.get_listen_address(st_conf_file)
      toks = listen_address.split(':')
      port = int(toks[2]) if len(toks) == 3 else None
      p = self.get_available_port(host, port)
      if p != port:
        listen_address = ':'.join(['tcp://' + host, str(p)])
        self.set_listen_address(st_conf_file, listen_address)
      
    #opts.append('-gui-address')
    #opts.append(gui_address)

    os.environ['HOME'] = os.path.expanduser('~')
    os.environ['STNOUPGRADE'] = '1'
    DEVNULL = open(os.devnull, 'w') 
    process = subprocess.Popen(opts, stdout=DEVNULL)

    return new_flag

  def delete_default_folder(self):
    home_dir = os.path.expanduser('~')
    sync_folder = os.path.join(home_dir, 'Sync')
    self.delete_platform_folder(
      folder_path=sync_folder, 
      config_path=self.st_conf_file,
      force_config=True
    )

  def autostart(self, folder_path):

    HOME = self.home_dir
    DEVNULL = open(os.devnull, 'w')
    bin_binary = os.path.join(HOME, 'bin', self.st_binary)

    # == ln -s ~/.st/.../syncthing ~/bin/syncthing
    if not os.path.exists(bin_binary):

      # NOTE: this avoids a race condition if directory is created
      # before attempting to create it here. That will raise an OSError.
      # If directory already exists, pass
      try:
        os.makedirs(os.path.join(HOME, 'bin'))

      except OSError as exception:
        if exception.errno != errno.EEXIST:
          raise

      os.symlink(os.path.join(folder_path, self.st_binary), bin_binary)

    # == ~/Library/LaunchAgents/com.kodrive.autostart.plist
    agent_path = os.path.join(HOME, 'Library/LaunchAgents')

    try:
      os.makedirs(agent_path)

    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

    plist_name = 'com.kodrive.autostart'
    plist_path = os.path.join(agent_path, plist_name + '.plist')

    # if no plist, create it
    if not os.path.isfile(plist_path):
      plist = mac_plist_adt.PList(plist_name, HOME, bin_binary)
      plistlib.writePlist(plist.file, plist_path)

    # NOTE: fails if running on a headless VM, for most
    # practical purposes, will not occur
    p = subprocess.Popen([
      'launchctl', 'load', plist_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    daemon_list = subprocess.check_output([
      'launchctl', 'list'
    ])

    if plist_name not in daemon_list:
      raise custom_errors.StartOnLoginFailure()

    DEVNULL.close()

  # Not used, kept for reference
  def disable_autostart(self):

    HOME = os.path.expanduser('~')
    DEVNULL = open(os.devnull, 'w')
    agent_path = os.path.join(HOME, 'Library/LaunchAgents')
    plist_name = 'com.kodrive.autostart'
    plist_path = os.path.join(agent_path, plist_name + '.plist')

    if os.path.isfile(plist_path):
      p = subprocess.Popen([
        'launchctl', 'unload', plist_path
      ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      out, err = p.communicate()

    daemon_list = subprocess.check_output([
      'launchctl', 'list'
    ], stderr=subprocess.STDOUT)

    if plist_name in daemon_list:
      raise custom_errors.StartOnLoginFailure()

    os.remove(plist_path)
    DEVNULL.close()

# class SyncthingWin64():
  # TODO



