class RollbackerBase(object):
  
  def __init__(self, handler):
    self.app_handler = handler

class AppRollbacker(RollbackerBase):
  
  def __init__(self, handler):
    super(AppRollbacker, self).__init__(handler)
    self.app_config = handler.adapter.get_config()
    
  def rollback_config(self):
    self.app_handler.wait_start(0.5, 10)
    self.app_handler.adapter.set_config(self.app_config)

    if self.app_handler.ping():
      self.app_handler.restart()

    self.app_handler.wait_start(0.5, 15)

class SyncthingRollbacker(RollbackerBase):
  
  def __init__(self, handler):
    super(SyncthingRollbacker, self).__init__(handler)
    self.syncthing_config = handler.get_config()

  def rollback_config(self):
    self.app_handler.wait_start(0.5, 10)
    self.app_handler.set_config(self.syncthing_config)

    if self.app_handler.ping():
      self.app_handler.restart()

    self.app_handler.wait_start(0.5, 15)
    
