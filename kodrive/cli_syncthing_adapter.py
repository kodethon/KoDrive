from .data import custom_errors
from .data import config
from .utils import config_rollbacker as rb
from . import syncthing_factory as factory

import click, time
import json, os, traceback

# This class is no longer used as a 
# result of the new subcommand system
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
    
    #if not self.handler.wait_start(0.5, 10, verbose=True):
    #  raise custom_errors.CannotConnect()

    self.handler.make_server()
    return 'KodeDrive now running in server mode.'

  def client(self):

    #if not self.handler.wait_start(0.5, 10, verbose=True):
    #  raise custom_errors.CannotConnect()

    self.handler.make_client()
    return 'KodeDrive now running in client mode.'

  def autostart(self):

    if not self.handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    self.handler.autostart()

def link(**kwargs):
  handler = factory.get_handler()

  # Save application state in case of error
  app_rb = rb.AppRollbacker(handler)
  st_rb = rb.SyncthingRollbacker(handler)

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()
    
    md = handler.decode_key(kwargs['key'])

    if not md:
      raise KeyError('Invalid Key.')
    
    device_id = md['devid']
    
    # Server - client
    if 'remote_path' in md and 'api_key' in md:
      remote_path = md['remote_path']
      api_key = md['api_key']
      tag = handler.link(
        device_id=device_id,
        api_key=api_key, 
        tag=kwargs['tag'], 
        local_path=kwargs['path'],
        remote_path=remote_path,
        interval=kwargs['interval'],
        remote_port=md['port'] if 'port' in md else None
      )
    # Client - client
    elif 'label' in md and 'folder_id' in md and 'hostname' in md:
      label = md['label']
      hostname = md['hostname']
      folder_id = md['folder_id']
      tag = (kwargs['tag'] or label)

      handler.acknowledge(
        device_id=device_id,
        hostname=hostname,
        label=tag,
        r_folder_id=folder_id,
        local_path=kwargs['path'],
        interval=kwargs['interval']
      )
    else:
      return 'Invalid Key.', True
    
    return ("%s (%s) is now being synchronized." % (kwargs['path'], tag)), False
  except ValueError as e:
    return e.message, True
  except KeyError as e:
    return e.message, True
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()
    
    # Error! Rollback :/
    if handler.ping():
      click.echo('An error occurred. Rolling back...') 
      app_rb.rollback_config()
      st_rb.rollback_config()

    return e.message, True

SystemSingleton = SystemFactory()
def sys(**kwargs):
  
  sub_handlers = {
    'client' : SystemSingleton.client,
    'exit' : SystemSingleton.exit,
    'restart' : SystemSingleton.restart,
    'server' : SystemSingleton.server,
    'test' : SystemSingleton.test,
  }
    
  try:
    for key in kwargs:
      # Map option to handler
      if(kwargs[key]):
        sub_handler = sub_handlers[key]

        # Check if arg is a flag 
        if type(kwargs[key]) == bool:
          return sub_handler(), False
        else:
          return sub_handler(kwargs[key]), False

    return None, False
  except Exception as e:
    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True
  
def refresh(**kwargs):
  handler = factory.get_handler()
  path = kwargs['path']

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    success = handler.scan(path)

    if 'progress' in kwargs:
      return handler.completion(path, kwargs['device_num']), False
    else:
      return (None, False) if success else ('Failed to refresh ' + path, True)
    
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

def free(path):
  handler = factory.get_handler()
  app_rb = None
  st_rb = None

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()
  
    # Save application state in case of error
    app_rb = rb.AppRollbacker(handler)
    st_rb = rb.SyncthingRollbacker(handler)

    handler.free(path)
    return "%s is no longer being synchronized." % path, False

  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()
    
    return e.message, True

  else:
    if handler.ping():
      app_rb.rollback_config()
      st_rb.rollback_config()

def tag(path, name):
  handler = factory.get_handler()

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    prev_name = handler.tag(path, name)
    
    return "%s has been changed to %s" % (prev_name, name), False
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

def ls(): 
  handler = factory.get_handler()

  metadata = handler.ls()

  if not metadata:
    return None, None

  headers = []
  lengths = []

  # Preprocess

  # Iterate through list
  for i, record in enumerate(metadata):
    lengths.append(0)

    # Iterate through dictionary
    for header in record:
      headers.append(header)
      num_data = len(record[header])

      for data in record[header]:
        cur = len(data)
        prev = lengths[i] 

        lengths[i] = cur if cur > prev else prev
  
  # Process
  body = str()
  for i in range(0, num_data):
    for n in range(0, len(metadata)):
      value = metadata[n][headers[n]][i]
      s = "{:<%i}" % (lengths[n] + 5)
      body += s.format(value.strip())

    body += "\n"
  
  if len(body) == 0:
    return None, None

  heading = str()
  # Iterate through list
  for i, record in enumerate(metadata):
    # Iterate through dictionary
    for header in record:
      s = "{:<%i}" % (lengths[i] + 5)
      heading += s.format(header)

  return heading, body

def key(**kwargs):
    
  handler = factory.get_handler()
  
  try:
    # Return device key
    if 'device' in kwargs:
      return handler.encode_device_key(), False

    # Return folder key
    elif 'folder' in kwargs:
      path = handler.to_st_path(kwargs['folder'])
      
      if not handler.adapter.folder_exists(path):
        raise custom_errors.FileNotInConfig(path)
      
      client = False
      server = False

      if kwargs['client']:
      	client = True

      if kwargs['server']:
      	server = True

      return handler.encode_key(path, client, server), False

    # Else display help
    else:
      return None, False
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

def add(**kwargs):
  
  handler = factory.get_handler()

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()
    
    kwargs['wait'] = True
    handler.add(**kwargs)
    return ("You can now share %s" % kwargs['path']), False
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

def mv(source, target):
  handler = factory.get_handler()

  try:
    if not handler.wait_start(0.5, 10, verbose=True):
      raise custom_errors.CannotConnect()

    if os.path.isdir(target) or os.path.islink(target):
      return handler.move(source, target), False
      # if target is an existing directory or symbolic link then move()

    else:
      return handler.rename(source, target), False

  except Exception as e:
    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

# This should be placed here
def mv_edge_case(source, target):
  handler = factory.get_handler()

  try:
    return handler.mv_edge_case(source, target)

  except Exception as e:
    if not config.Flags['production']:
      traceback.print_exc()

    return e.message

def auth(option, key, path):
  handler = factory.get_handler()

  try:
    if option == 'add':
      handler.auth(key, path)
      hostname = handler.decode_device_key(key)['hostname']

      return "%s can now access %s." % (hostname, path), False
    elif option == 'remove':
      handler.deauth(key, path)
      hostname = handler.decode_device_key(key)['hostname']

      return ("%s can no longer access %s" % (hostname, path)), False
    elif option == 'list':
      return handler.auth_ls(), False
    else:
      return None, False
  except Exception as e:

    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

def info(**kwargs):
  handler = factory.get_handler()

  try:
    # Get folder infomation
    if 'folder' in kwargs:
      if not handler.wait_start(0.5, 10, verbose=True):
        raise custom_errors.CannotConnect()

      return handler.stat(kwargs['folder']), False

    # Get system information
    elif 'device' in kwargs:
      kodrive_config = handler.adapter.get_config()
      is_server = kodrive_config['system']['server']
      
      if handler.ping():
        config_path = handler.adapter.st_conf_file
        address = handler.adapter.get_gui_address(config_path)
        return ('Running as %s at %s.' % ('server' if is_server else 'client', address)), False
      else:
        return ('Exited as %s.' % ('server' if is_server else 'client')), True
    else:
      return None, False

  except Exception as e:
    if not config.Flags['production']:
      traceback.print_exc()

    return e.message, True

def start(**kwargs):
  handler = factory.get_handler()

  try:
    handler.live_update()
  except Exception as e:
    click.echo(e)

  if not handler.ping():
    if not handler.start(**kwargs):
      return 'KodeDrive could not be started.', True
    else:
      handler.autostart()
      return 'KodeDrive has successfully started.', False
  else:
    return 'KodeDrive has already been started.', False
