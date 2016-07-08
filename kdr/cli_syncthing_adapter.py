import syncthing_factory as factory
import json

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

def link(key, name, path):
  handler = factory.get_handler()
  
  try:
    name = handler.link(key, name, path)
    return "%s (%s) is now being synchronized." % (path, name)
  except Exception as e:
    return e.message

def info(**kwargs):
  handler = factory.get_handler()

  if kwargs['status']:
    info = 'Running' if handler.ping() else 'Exited'

  elif kwargs['key']:
    key = handler.encode_key()
    info = handler.encode_key()

  return info

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
    handler.unlink(path)
    return "%s is no longer being synchronized." % path
  except Exception as e:
    return e.message

def rename(source, target):
  handler = factory.get_handler()

  # try:
  return handler.rename(source, target)
  # except Exception as e:
    # return e.message

    
def test(arg):
  handler = factory.get_handler()
  return handler.test(arg)
