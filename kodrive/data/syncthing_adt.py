
class Folder:

  def __init__(self, **kwargs):
    if 'rescanIntervalS' in kwargs:
      rescanIntervalS = kwargs['rescanIntervalS']   
    else:
      rescanIntervalS = 30

    self.folder = {
      'rescanIntervalS' : rescanIntervalS,
      'copiers' : 0,
      'pullerPauseS' : 0,
      'autoNormalize' : True,
      'id' : kwargs['id'] ,
      'scanProgressIntervalS' : 0,
      'hashers' : 0,
      'pullers' : 0,
      'invalid' : '',
      'label' : kwargs['label'],
      'minDiskFreePct' : 1,
      'pullerSleepS' : 0,
      'type' : 'readwrite',
      'disableSparseFiles' : False,
      'path' : kwargs['path'],
      'ignoreDelete' : False,
      'ignorePerms' : False,
      'devices' : [{'deviceID' : kwargs['deviceID']}],
      'disableTempIndexes' : False,
      'maxConflicts' : 10,
      'order' : 'random',
      'versioning' : {'type': '', 'params': {}}
    }

    for key in kwargs:
      self.folder[key] = kwargs[key]
  
  @property
  def obj(self):
    return self.folder

  def add_device(self, deviceID):
    self.folder['devices'].append({
      'deviceID' : deviceID
    })
