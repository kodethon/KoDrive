from data import custom_errors
from data import config
from utils import config_rollbacker as rb
import syncthing_factory as factory

import click, time
import json, os, traceback

class SystemFactory:
  
  def __init__(self):
    self.handler = factory.get_handler()

  def restart(self):
    handler = factory.get_handler()

    if not handler.ping():
      raise custom_errors.CannotConnect()

    handler.restart()
    
    click.echo("KodeDrive is now restarting.")

    count = 0
    limit = 10
    while not handler.ping() and count < limit:
      click.echo("Attempting to detect Kodedrive...") 
      count += 1
      time.sleep(1)

    if count >= limit:
      return "Could not restart KodeDrive :("
    else:
      return "KodeDrive has successfully restarted!"

  def delay(self, secs):
    if not self.handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()
    
    success = self.handler.set_rescan_interval(secs)

    if success:
      return 'KodeDrive will now sync every %s seconds.' % secs
    else:
      return 'Seconds cannot be negative.'

  def init(self):
    if not self.handler.ping():
      if not self.handler.start():
        return 'KodeDrive could not be started.'
      else:
        return 'KodeDrive has successfully started.'
    else:
      return 'KodeDrive has already been started.' 

  def about(self):
    kdr_config = self.handler.adapter.get_config()
    is_server = kdr_config['system']['server']
    
    if self.handler.ping():
      config_path = self.handler.adapter.st_conf_file
      address = self.handler.adapter.get_gui_address(config_path)
      return 'Running as %s at %s.' % ('server' if is_server else 'client', address)
    else:
      return 'Exited as %s.' % ('server' if is_server else 'client')

  def key(self):
    if not self.handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    return self.handler.encode_device_key()
  
  def test(self, arg):
    return self.handler.test(arg)

  def exit(self):
    try:
      alive = self.handler.ping()
    except:
      alive = False

    if not alive:
      return 'KodeDrive has already exited.'

    if self.handler.shutdown():
      return 'KodeDrive has now exited.'  
    else: 
      return 'KodeDrive could not be stopped.'
  
  def server(self):
    
    if not self.handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    self.handler.make_server()
    return 'KodeDrive now running in server mode.'

  def client(self):

    if not self.handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    self.handler.make_client()
    return 'KodeDrive now running in client mode.'

def link(key, tag, path):
  handler = factory.get_handler()

  # Save application state in case of error
  app_rb = rb.AppRollbacker(handler)
  st_rb = rb.SyncthingRollbacker(handler)

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()
    
    md = handler.decode_key(key)

    if not md:
      raise KeyError('Invalid Key.')
    
    device_id = md['devid']

    if 'remote_path' in md and 'api_key' in md:
      remote_path = md['remote_path']
      api_key = md['api_key']
      tag = handler.link(
        device_id=device_id,
        api_key=api_key, 
        tag=tag, 
        local_path=path,
        remote_path=remote_path
      )
    elif 'label' in md and 'folder_id' in md and 'hostname' in md:
      label = md['label']
      hostname = md['hostname']
      folder_id = md['folder_id']
      tag = (tag or label)

      handler.acknowledge(
        device_id=device_id,
        hostname=hostname,
        label=tag,
        r_folder_id=folder_id,
        local_path=path
      )

    return "%s (%s) is now being synchronized." % (path, tag)
  except KeyError as e:
    return e.message
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    app_rb.rollback_config()
    st_rb.rollback_config()
    return e.message

SystemSingleton = SystemFactory()
def sys(**kwargs):
  
  sub_handlers = {
    'about' : SystemSingleton.about,
    'client' : SystemSingleton.client,
    'exit' : SystemSingleton.exit,
    'init' : SystemSingleton.init,
    'key' : SystemSingleton.key,
    'restart' : SystemSingleton.restart,
    'server' : SystemSingleton.server,
    'test' : SystemSingleton.test,
    'delay' : SystemSingleton.delay
  }
    
  try:
    for key in kwargs:
      if(kwargs[key]):
        sub_handler = sub_handlers[key]

        if type(kwargs[key]) == bool:
          return sub_handler()
        else:
          return sub_handler(kwargs[key])
  except Exception as e:
    if not config.Flags['production']:
      traceback.print_exc()

    return e.message
  
def refresh(**kwargs):
  handler = factory.get_handler()
  path = kwargs['path']

  try:
    success = handler.scan(path)

    if 'progress' in kwargs:
      return handler.completion(path, kwargs['device_num'])
    else:
      return None if success else 'Failed to refresh ' + path
    
  except IOError as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message

def free(path):
  handler = factory.get_handler()

  # Save application state in case of error
  app_rb = rb.AppRollbacker(handler)
  st_rb = rb.SyncthingRollbacker(handler)

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()
    
    handler.free(path)
    return "%s is no longer being synchronized." % path
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    app_rb.rollback_config()
    st_rb.rollback_config()
    return e.message

def tag(path, name):
  handler = factory.get_handler()

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    prev_name = handler.tag(path, name)
    
    return "%s has been changed to %s" % (prev_name, name)
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message

def ls(): 
  handler = factory.get_handler()

  return handler.ls()

def key(path):

  if not path[len(path) - 1] == '/':
    path += '/'

  handler = factory.get_handler()
  if not handler.wait_start(0.5, 10, verbose=True):
    raise custom_errors.CannotConnect()

  try:
    if not handler.folder_exists({
      'path': path
    }):
      raise custom_errors.FileNotInConfig(path)
      
    return handler.encode_key(path)
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message

def add(**kwargs):
  
  handler = factory.get_handler()

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    handler.add(**kwargs)
    return "You can now share %s" % kwargs['path']
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message

def mv(source, target):
  handler = factory.get_handler()

  if os.path.isdir(target) or os.path.islink(target):
    return handler.move(source, target)
    # if target is an existing directory or symbolic link then move()

  else:
    return handler.rename(source, target)

def mv_edge_case(source, target):
  handler = factory.get_handler()

  return handler.mv_edge_case(source, target)

def auth(option, key, path):
  handler = factory.get_handler()

  try:
    if option == 'add':
      handler.auth(key, path)
      hostname = handler.decode_device_key(key)['hostname']
      return "%s can now access %s." % (hostname, path)

    elif option == 'remove':
      handler.deauth(key, path)
      hostname = handler.decode_device_key(key)['hostname']
      return "%s can no longer access %s" % (hostname, path)

    elif option == 'list':
      return handler.auth_ls()
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message

def stat(**kwargs):
  handler = factory.get_handler()

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    path = kwargs['path']

    return handler.stat(path)
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message


"""

def start():

  try:
    handler = factory.get_handler()
    alive = handler.ping()
  except Exception as e:
    alive = False
  
  if not alive:
    success = handler.start()   

    if not success:
      return e if e else 'KodeDrive could not be started.'

    else:
      return 'KodeDrive has successfully started.'

  else:
    return 'KodeDrive has already been started.' 

def stop():
        
  handler = factory.get_handler()

  try:
    alive = handler.ping()

  except:
    alive = False

  if not alive:
    return 'KodeDrive has already exited.'

  return handler.shutdown()

"""
