
from syncthing import Syncthing

import xml.etree.ElementTree as ET
import os, subprocess

class SyncthingLinux64(): 
    
    binary = 'syncthing'

    def create_config(self, key, name, path):
        home_dir = os.path.expanduser('~')
        folder_path = os.path.join(home_dir, '.config/kdr')
        config_path = os.path.join(folder_path, 'config.json')
        
        name = hashlib.sha1(key).hexdigest() if not name else name

        record = {
            name : {
                'local_path' : path,
                'remote_key' : key
            }
        }
        
        # If config file does not exist, create it
        # And then add the new directory data into it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
            config = {
                'directories' : [record]
            }

            fp = open(config_path, 'w')
            fp.write(json.dumps(config))
            fp.close
        else:
            
            with open(config_path, "r+") as f:
                raw = f.read()
                f.seek(0)
                config = json.loads(raw)
                config['directories'].append(record)
                f.write(json.dumps(config))
                f.truncate()

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
        linux_64_bit_file = 'syncthing-linux-amd64-v0.13.7'
        syncthing_path = os.path.join(dest, linux_64_bit_file)
        
        # If syncthing doesn't exist, install it
        if not os.path.exists(syncthing_path):
            dest_tmp = '/tmp'
            linux_64_bit_repo = 'https://github.com/syncthing/syncthing/releases/tag/v0.13.7'
            linux_64_bit_tar = 'syncthing-linux-amd64-v0.13.7.tar.gz'

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

class SyncthingMac64():
    binary = 'syncthing'

    # TODO: Check if all functions work for Mac OSX
    def create_config(self, key, name, path):
        home_dir = os.path.expanduser('~')
        folder_path = os.path.join(home_dir, '.config/kdr')
        config_path = os.path.join(folder_path, 'config.json')
        
        name = hashlib.sha1(key).hexdigest() if not name else name

        record = {
            name : {
                'local_path' : path,
                'remote_key' : key
            }
        }
        
        # If config file does not exist, create it
        # And then add the new directory data into it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
            config = {
                'directories' : [record]
            }

            fp = open(config_path, 'w')
            fp.write(json.dumps(config))
            fp.close

        else:
            with open(config_path, "r+") as f:
                raw = f.read()
                f.seek(0)
                config = json.loads(raw)
                config['directories'].append(record)
                f.write(json.dumps(config))
                f.truncate()

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
        mac_64_bit_file = 'syncthing-macosx-amd64-v0.13.7'
        syncthing_path = os.path.join(dest, mac_64_bit_file)
        
        # If syncthing doesn't exist, install it
        if not os.path.exists(syncthing_path):
            dest_tmp = '/tmp'
            mac_64_bit_repo = 'https://github.com/syncthing/syncthing/releases/download/v0.13.7'
            mac_64_bit_tar = 'syncthing-macosx-amd64-v0.13.7.tar.gz'

            # Mac OSX doesn't come preinstalled with wget, so we use curl
            command = "curl -L -o %s/%s \"%s/%s\"" % (dest_tmp, mac_64_bit_tar, mac_64_bit_repo, mac_64_bit_tar)
            subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

            src = dest_tmp
            command = "sudo tar -zxvf %s/%s --directory %s" % (src, mac_64_bit_tar, dest)
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

