import custom_errors
import syncthing_factory as factory

import json, os

def link(key, name, path):
  handler = factory.get_handler()

  #try:

  if not handler.ping():
    raise custom_errors.CannotConnect()

  name = handler.link(key, name, path)
  return "%s (%s) is now being synchronized." % (path, name)
  #except Exception as e:
  #  return e.message

def sys(**kwargs):
  handler = factory.get_handler()

  if kwargs['start']:

    try:
      handler = factory.get_handler()
      alive = handler.ping()
    except Exception as e:
      print e
      alive = False
    
    if not alive:
      success = handler.start()   

      if not success:
        return 'KodeDrive could not be started.'
      else:
        return 'KodeDrive has successfully started.'
    else:
      return 'KodeDrive has already been started.' 
  
  if kwargs['check']:
    return 'Running' if handler.ping() else 'Exited'

  if kwargs['test']:
    return handler.test(kwargs['test'])

  if kwargs['exit']:
    try:
      alive = handler.ping()
    except:
      alive = False

    if not alive:
      return 'KodeDrive has already exited.'

    if handler.shutdown():
      return 'KodeDrive has now exited.'  
    else: 
      return 'KodeDrive could not be stopped.'

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
