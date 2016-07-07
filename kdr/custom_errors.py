class KodeDriveError(Exception):
  application = 'KodeDrive'
    
class FileNotInConfig(KodeDriveError):

  def __init__(self, f_path):
    super(Exception, self).__init__(
      "%s could not find %s." % (self.application, f_path)
    )

class DeviceNotFound(KodeDriveError):

  def __init__(self, hostname):
     
    super(ValidationError, self).__init__(
        "%s could not finde %s." % (self.applicatio, hostname)
    )

