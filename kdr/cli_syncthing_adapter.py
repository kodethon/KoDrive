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

def init(key, name, path):
    handler = factory.get_handler()
    return handler.init(key, name, path)

def info(**kwargs):
    handler = factory.get_handler()

    if kwargs['status']:
     	info = 'Running' if handler.ping() else 'Exited'
    elif kwargs['key']:
    	key = handler.encode_key()
    	info = handler.encode_key()

    return info

def refresh(path):
    handler = factory.get_handler()

    return handler.scan(path)

def test(arg):
    handler = factory.get_handler()
    return handler.test(arg)
