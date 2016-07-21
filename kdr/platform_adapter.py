from py_syncthing_adapter import Syncthing
from data import custom_errors

import xml.etree.ElementTree as ET
import os, subprocess
import json, hashlib
import urllib, copy

class PlatformBase(object):

  app_config = 'config.json'
  st_config = 'config.xml'
  st_binary = 'syncthing'
  stfolder = '.stfolder'
  st_version = '0.13.9'
  #st_version = '0.14.0-beta.1'
  default_config = {
    'directories' : {},
    'system' : {
      'server' : False
    }
  }

  def get_gui_address(self, config_path):   
    tree = ET.parse(config_path)
    return tree.find('gui').find('address').text

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
      dir_id = self.get_dir_id(local_path.rstrip('/'))

      try:
        return config['directories'][dir_id]
      except:
        custom_errors.FileNotInConfig(local_path)
  
  def set_gui_address(self, config_path, address):
    tree = ET.parse(config_path)
    tree.find('gui').find('address').text = address
    ET.write(tree)

  def get_platform_gui_hook(self, config_path):
    tree = ET.parse(config_path)
    api_key = tree.find('gui').find('apikey').text
    address = tree.find('gui').find('address').text
    toks = address.split(':')
    host = toks[0]
    port = toks[1]

    return Syncthing(api_key=api_key, port=int(port), host=host)

  def get_platform_device_id(self, config_path):
    tree = ET.parse(config_path)
    return tree.find('device').items()[0][1]
  
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
      'label' : object['label'],
      'local_path' : object['local_path'],
      'remote_path' : object['remote_path'] if 'remote_path' in object else '',
      'is_shared' : object['is_shared']
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

  def rename_dir(self, object, source_path, target_path):
    source_path = source_path.rstrip('/')
    target_path = target_path.rstrip('/')
    home_dir = os.path.expanduser('~')
    folder_path = os.path.join(home_dir, '.config/kdr')
    metadata = self.create_dir_metadata(object)
    record = self.create_dir_record(object, metadata)
    config_path = os.path.join(folder_path, self.app_config)

    with open(config_path, "r+") as f:
      raw = f.read()
      f.seek(0)
        
      if len(raw) > 0:

        try:
          config = json.loads(raw)
        except Exception as e:
          raise IOError("Corrupted config.json file in %s" % folder_path)

        try:
          del config['directories'][self.get_dir_id(source_path)]
        except:
          custom_errors.InvalidKey(self.get_dir_id(source_path))

        name = self.get_dir_id(target_path)
        config['directories'][name] = metadata
        # deletes old element, adds new element with different name and path

        f.write(json.dumps(config))
        f.truncate()

        # TODO: Should handle corrupt config files later

      else:
        config = self.create_config(folder_path, directories=record)

class SyncthingLinux64(PlatformBase): 
  
  rel_st_conf_dir = '.config/syncthing'
  rel_app_conf_dir  = '.config/kdr'
  
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
    return self.get_platform_device_id(self.st_conf_file)

  def get_syncthing_path(self):
    dest = '/var/opt'
    linux_64_bit_file = "syncthing-linux-amd64-v%s" % self.st_version
    syncthing_path = os.path.join(dest, linux_64_bit_file)

    # If syncthing doesn't exist, install it
    if not os.path.exists(syncthing_path):
      dest_tmp = '/tmp'
      linux_64_bit_repo = "https://github.com/syncthing/syncthing/releases/download/v%s" % self.st_version
      linux_64_bit_tar = "syncthing-linux-amd64-v%s.tar.gz" % self.st_version

      command = "wget -P %s %s/%s" % (dest_tmp, linux_64_bit_repo, linux_64_bit_tar)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

      src = dest_tmp
      command = "sudo tar -zxvf %s/%s --directory %s" % (src, linux_64_bit_tar, dest)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    return syncthing_path

  def start_syncthing(self, folder_path):   
    
    new_flag = False

    command = os.path.join(folder_path, self.st_binary)
    opts = [command, '-no-browser', '-home', self.app_conf_dir]

    if not os.path.exists(self.st_conf_file):
      new_flag = True
    else:  
      gui_address = self.get_gui_address(self.st_conf_file)
      opts.append('-gui-address')
      opts.append(gui_address)

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

class SyncthingMac64(PlatformBase): 

  rel_st_conf_dir = 'Library/Application Support/Syncthing'
  rel_app_conf_dir  = '.config/kdr'

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
    return self.get_platform_device_id(self.st_conf_file)

  def get_syncthing_path(self):
    dest = '/usr/local' # external applications folder
    mac_64_bit_file = "syncthing-macosx-amd64-v%s" % self.st_version
    syncthing_path = os.path.join(dest, mac_64_bit_file)
    
    # If syncthing doesn't exist, install it
    if not os.path.exists(syncthing_path):
      dest_tmp = '/tmp'
      mac_64_bit_repo = "https://github.com/syncthing/syncthing/releases/download/v%s" % self.st_version
      mac_64_bit_tar = "syncthing-macosx-amd64-v%s.tar.gz" % self.st_version

      link = mac_64_bit_repo + '/' + mac_64_bit_tar
      urllib.urlretrieve(link, os.path.join(dest_tmp, mac_64_bit_tar))
      # Download from site

      src = dest_tmp
      command = "tar -zxvf %s/%s --directory %s" % (src, mac_64_bit_tar, dest)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    return syncthing_path

  def start_syncthing(self, folder_path):   
    
    new_flag = False

    command = os.path.join(folder_path, self.st_binary)
    opts = [command, '-no-browser', '-home', self.st_conf_dir]

    if not os.path.exists(self.st_conf_file):
      new_flag = True
    else:  
      gui_address = self.get_gui_address(self.st_conf_file)
      opts.append('-gui-address')
      opts.append(gui_address)

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

# class SyncthingWin64():
  # TODO

