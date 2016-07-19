import custom_errors
import syncthing_factory as factory

import json, os

class SystemFactory:
  
  def __init__(self):
    self.handler = factory.get_handler()

  def init(self):
    if not self.handler.ping():
      if not self.handler.start():
        return 'KodeDrive could not be started.'
      else:
        return 'KodeDrive has successfully started.'
    else:
      return 'KodeDrive has already been started.' 
  
  def list(self):
    kdr_config = self.handler.adapter.get_config()
    is_server = kdr_config['system']['server']
    
    if self.handler.ping():
      return 'Running as %s.' % ('server' if is_server else 'client')
    else:
      return 'Exited as %s.' % ('server' if is_server else 'client')
  
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
    
    if not self.handler.ping():
      raise custom_errors.CannotConnect()

    self.handler.make_server()
    return 'KodeDrive now running in server mode.'

  def client(self):

    if not self.handler.ping():
      raise custom_errors.CannotConnect()

    self.handler.make_client()
    return 'KodeDrive now running in client mode.'

def link(key, tag, path):
  handler = factory.get_handler()

  #try:

  if not handler.ping():
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
  #except Exception as e:
  #  return e.message

SystemSingleton = SystemFactory()
def sys(**kwargs):
  
  sub_handlers = {
    'client' : SystemSingleton.client,
    'exit' : SystemSingleton.exit,
    'init' : SystemSingleton.init,
    'list' : SystemSingleton.list,
    'server' : SystemSingleton.server,
    'test' : SystemSingleton.test
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
    return e.message
  
def refresh(**kwargs):
  handler = factory.get_handler()

  if 'progress' in kwargs:
    return handler.completion()

  path = kwargs['path']

  try:
    success = handler.scan(path)
    return None if success else 'Failed to refresh ' + path
    
  except IOError as e:
    return e.message

def unlink(path):
  handler = factory.get_handler()
  
  try:
    if not handler.ping():
      raise custom_errors.CannotConnect()

    handler.unlink(path)
    return "%s is no longer being synchronized." % path
  except Exception as e:
    return e.message

def tag(path, name):
  handler = factory.get_handler()

  try:
    if not handler.ping():
      raise custom_errors.CannotConnect()

    prev_name = handler.tag(path, name)
    
    return "%s has been changed to %s" % (prev_name, name)
  except Exception as e:
    return e.message

def ls(): 
  handler = factory.get_handler()

  return handler.ls()

def key(path):

  if not path[len(path) - 1] == '/':
    path += '/'

  handler = factory.get_handler()
    
  try:
    if not handler.folder_exists({
      'path': path
    }):
      raise custom_errors.FileNotInConfig(path)
      
    return handler.encode_key(path)
  except Exception as e:
    return e.message

def add(**kwargs):
  
  handler = factory.get_handler()

  try:
    if not handler.ping():
      raise custom_errors.CannotConnect()

    handler.add(**kwargs)
    return "You can now share %s" % kwargs['path']
  except Exception as e:
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

def auth(path, key):
  handler = factory.get_handler()
  
  # try:
  handler.auth(path, key)
  return "%s can now access %s." % (key, path)
  # except Exception as e:
    # return e.message

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
