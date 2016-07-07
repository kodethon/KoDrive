from py_syncthing_adapter import Syncthing

import xml.etree.ElementTree as ET
import os, subprocess
import json, hashlib
import urllib

class PlatformBase():

  binary = 'syncthing'
  config = 'config.json'

  def update_platform_config(self, folder_path, object):

    # If config file does not exist, create it
    # And then add the new directory data into it
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)

      metadata = self.create_dir_metadata(object)
      record = self.create_dir_record(object, metadata)

      self.create_config(folder_path, record) 

    else:
      self.append_dir_metadata(folder_path, object)
  
  def create_config(self, folder, record):
    config_path = os.path.join(folder, self.config) 
    config = {
      'directories' : record
    }

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
      'remote_path' : object['remote_path']
    }

  def create_dir_record(self, object, metadata):
    
    name = self.get_dir_id(object)
    return {name : metadata}

  def append_dir_metadata(self, folder_path, object):

    metadata = self.create_dir_metadata(object)
    record = self.create_dir_record(object, metadata)
    config_path = os.path.join(folder_path, self.config)

    with open(config_path, "r+") as f:
      raw = f.read()
      f.seek(0)
        
      if len(raw) > 0:
        config = json.loads(raw)

        name = self.get_dir_id(object)
        config['directories'][name] = metadata

        f.write(json.dumps(config))
        f.truncate()
        
        # TODO: Should handle corrupt config files later

      else:
        config = self.create_config(folder_path, record)

  def get_dir_id(self, object):
    if 'name' in object and not object['name'] == None:
        return object['name']
    else:
        return hashlib.sha1(object['local_path']).hexdigest()

class SyncthingLinux64(PlatformBase): 

  def update_config(self, object):
    home_dir = os.path.expanduser('~')
    folder_path = os.path.join(home_dir, '.config/kdr')

    self.update_platform_config(folder_path, object)

  def get_dir_config(self, local_path):
    home_dir = os.path.expanduser('~')
    folder_path = os.path.join(home_dir, '.config/kdr')
    config_path = os.path.join(folder_path, self.config) 
    
    try:
      with open(config_path, "r") as f:
        raw = f.read()
        config = json.loads(raw)
        dir_id = self.get_dir_id({
            'local_path' : local_path
        })

        return config['directories'][dir_id]
    except Exception as e:
      return None

  def get_gui_hook(self):
    home_dir = os.path.expanduser('~')
    tree = ET.parse(os.path.join(home_dir, '.config/syncthing/config.xml'))
    api_key = tree.find('gui').find('apikey').text
    address = tree.find('gui').find('address').text
    port = address.split(':')[1]

    return Syncthing(api_key=api_key, port=int(port))

  def get_device_id(self):
    home_dir = os.path.expanduser('~')
    tree = ET.parse(os.path.join(home_dir, '.config/syncthing/config.xml'))
    return tree.find('device').items()[0][1]

  def get_path(self):
    dest = '/var/opt'
    linux_64_bit_file = 'syncthing-linux-amd64-v0.13.9'
    syncthing_path = os.path.join(dest, linux_64_bit_file)

    # If syncthing doesn't exist, install it
    if not os.path.exists(syncthing_path):
      dest_tmp = '/tmp'
      linux_64_bit_repo = 'https://github.com/syncthing/syncthing/releases/download/v0.13.9'
      linux_64_bit_tar = 'syncthing-linux-amd64-v0.13.9.tar.gz'

      command = "wget -P %s %s/%s" % (dest_tmp, linux_64_bit_repo, linux_64_bit_tar)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

      src = dest_tmp
      command = "sudo tar -zxvf %s/%s --directory %s" % (src, linux_64_bit_tar, dest)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    return syncthing_path

  def start(self, folder_path):   
      
    command = os.path.join(folder_path, self.binary)

    DEVNULL = open(os.devnull, 'w') 
    process = subprocess.Popen([command, '-no-browser'], stdout=DEVNULL)
    is_success = (process.stderr == None)

    return is_success


class SyncthingMac64(PlatformBase): 
    
  binary = 'syncthing'
  config = 'config.json'

  def update_config(self, object):
    home_dir = os.path.expanduser('~')
    folder_path = os.path.join(home_dir, '.config/kdr')

    self.update_platform_config(folder_path, object)

  def create_config(self, folder, record):
    config_path = os.path.join(folder, self.config) 
    config = {
      'directories' : record
    }

    fp = open(config_path, 'w')
    fp.write(json.dumps(config))
    fp.close

    # What happens if write fails?

    return config

  def get_gui_hook(self):
    home_dir = os.path.expanduser('~')
    tree = ET.parse(os.path.join(home_dir, 'Library/Application Support/Syncthing/config.xml'))
    api_key = tree.find('gui').find('apikey').text
    address = tree.find('gui').find('address').text
    port = address.split(':')[1]

    return Syncthing(api_key=api_key, port=int(port))

  def get_device_id(self):
    home_dir = os.path.expanduser('~')
    tree = ET.parse(os.path.join(home_dir, 'Library/Application Support/Syncthing/config.xml'))
    return tree.find('device').items()[0][1]

  def get_path(self):
    dest = '/usr/local' # external applications folder
    mac_64_bit_file = 'syncthing-macosx-amd64-v0.13.9'
    syncthing_path = os.path.join(dest, mac_64_bit_file)
    
    # If syncthing doesn't exist, install it
    if not os.path.exists(syncthing_path):
      dest_tmp = '/tmp'
      mac_64_bit_repo = 'https://github.com/syncthing/syncthing/releases/download/v0.13.9'
      mac_64_bit_tar = 'syncthing-macosx-amd64-v0.13.9.tar.gz'

      link = mac_64_bit_repo + '/' + mac_64_bit_tar
      urllib.urlretrieve(link, mac_64_bit_tar)
      # Download from site

      src = dest_tmp
      command = "tar -zxvf %s/%s --directory %s" % (src, mac_64_bit_tar, dest)
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

    return syncthing_path

  def start(self, folder_path):   
    
    command = os.path.join(folder_path, self.binary)
    
    DEVNULL = open(os.devnull, 'w') 
    process = subprocess.Popen([command, '-no-browser'], stdout=DEVNULL)
    is_success = (process.stderr == None)

    return is_success


# class SyncthingWin64():
  # TODO

