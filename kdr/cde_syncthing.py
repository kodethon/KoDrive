from syncthing import Syncthing

# Self-defined
import src_proxy

# Standard library
import subprocess 
import os, sys
import xml.etree.ElementTree as ET
import json
import hashlib
import platform


class SyncthingFacade():
    
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
        
    def set_config(self, config):
        return self.sync.sys.set.config(config)

    def restart(self):
        self.sync.sys.set.restart();

    def start(self):    
        path = self.adapter.get_path()
        
        return self.adapter.start(path);

    def ping(self):
        # Silence stderr
        save_stderr = sys.stderr
        sys.stderr = open('trash', 'w')

        # Run command
        t = type(self.sync.sys.set.ping()) 
        sys.stderr = save_stderr

        return t == dict

    def shutdown(self):
        return self.sync.sys.set.shutdown()

    def name(self):
        try:
            return self.sync.sys.config()['devices'][0]['deviceID']
        except Exception:
            return self.adapter.get_device_id()

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
                key(str): remote device-id used to identify src
                name(str): user defined name associating key 
                path(str): path to folder user wants to sync
            
            returns success or failure

        """

        try:
            config = self.adapter.create_config(key, name, path)
            res = src_proxy.connect(self.name())

            if res.status == '200':
                return 'Success' 
            else:
                raise RuntimeError(res.body)
        except Exception, e:
            print str(e)
            return 'Failure'
     
    def test(self):
        sync = Syncthing(api_key='ACWpWrFTsgME52NAA7sHFeSfbvSKcCtG', port=8384)
        print sync
        return sync.sys.ping()


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

                
class SyncthingFactory:
    
    syncthing_posix = None
    syncthing_mac = None
    syncthing_win = None

    def __init__(self):
        if platform.system() == "Linux" or platform.system() == "Linux2":
            self.syncthing_posix = SyncthingFacade(SyncthingLinux64())
            # Linux
        elif platform.system() == "Darwin":
            self.syncthing_mac = SyncthingFacade(SyncthingMac64())
            # MacOSX
        elif platform.system() == "Windows":
            self.syncthing_win = SyncthingFacade(SyncthingWin64())
            # TODO: Windows

    def get_handler(self):
        handler = {
            'Linux' : self.syncthing_posix,
            'Darwin' : self.syncthing_mac,
            'Windows' : self.syncthing_win
        }.get(platform.system(), None)
        
        if not handler:
            raise Exception("%s is not currently supported." % platform.system())

        return handler

# Singleton
factory = SyncthingFactory()

def start():
    handler = factory.get_handler()

    try:
        alive = handler.ping()

    except Exception:
        alive = False

    finally:
        if not alive:
            success = handler.start()

            if not success:
                return 'An error has occurred'

            else:
                return handler.name()

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
    return handler.name()

def init(key, name, path):
    handler = factory.get_handler()
    return handler.init(key, name, path)

def test():
    handler = factory.get_handler()
    return handler.test()
