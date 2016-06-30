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
            return handler.name()
    else:
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
    return handler.get_device_id()

def init(key, name, path):
    handler = factory.get_handler()
    return handler.init(key, name, path)

def test():
    handler = factory.get_handler()
    return handler.test()
