from syncthing import Syncthing

import subprocess 
import os
import xml.etree.ElementTree as ET

class SyncthingFacade():
	
	sync = None
	adapter = None

	def __init__(self, adapter):

                self.adapter = adapter

	        try:
                    self.sync = adapter.get_gui_hook()
		except Exception:
		    return

	def get_config(self):	
		return self.sync.sys.config()
		
	def set_config(self, config):
		return self.sync.sys.set.config(config)

	def handshake(self):
		return

	def restart(self):
		self.sync.sys.set.restart();

	def start(self):	
		path = self.adapter.get_path()
		return self.adapter.start(path);

	def ping(self):
		return type(self.sync.sys.ping()) == dict

	def shutdown(self):
		return self.sync.sys.set.shutdown()

class SyncthingLinux64(): 
	
	binary = 'syncthing'
	
	def get_gui_hook(self):
		home_dir = os.path.expanduser('~')
		tree = ET.parse(os.path.join(home_dir, '.config/syncthing/config.xml'))
		api_key = tree.find('gui').find('apikey').text
		address = tree.find('gui').find('address').text
		port = address.split(':')[1]

		return Syncthing(api_key=api_key, port=int(port))

	def get_path(self):
		dest = '/var/opt'
		linux_64_bit_file = 'syncthing-linux-amd64-v0.13.7'
		syncthing_path = os.path.join(dest, linux_64_bit_file)
		
		# If syncthing doesn't exist, install it
		if not os.path.exists(syncthing_path):
			dest_tmp = '/tmp'
			linux_64_bit_tar = 'syncthing-linux-amd64-v0.13.7.tar.gz'

			command = "wget -P %s https://github.com/syncthing/syncthing/releases/download/v0.13.7/%s" % (dest_tmp, linux_64_bit_tar)
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
			
class SyncthingFactory:
	
	syncthing_posix = None
	
	def __init__(self):
		self.syncthing_posix = SyncthingFacade(SyncthingLinux64())

	def get_handler(self):
		handler = {
			'posix' : self.syncthing_posix
		}.get(os.name, None)

		if not handler:
			raise "%s is not currently supported." % os.name

		return handler

# Singleton
factory = SyncthingFactory()

def start():
	handler = factory.get_handler()
        success = True

        try:
            success = handler.ping()
        except Exception:
            success = False

	if not success:
		success = handler.start()

		if not success:
			return 'An error has occurred.'
		else:
			return 'Syncthing has started.'
	
	return 'Syncthing already started.'

def config():
	handler = factory.get_handler()
	
	return handler.get_config()

def stop():
	handler = factory.get_handler()

	return handler.shutdown()
