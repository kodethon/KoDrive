class KodeDriveError(Exception):
  application = 'KodeDrive'
    
class FileNotInConfig(KodeDriveError):

  def __init__(self, f_path):
    super(Exception, self).__init__(
      "%s could not find %s. Is it being synchronized?" % (self.application, f_path)
    )

class DeviceNotFound(KodeDriveError):

  def __init__(self, hostname):
     
    super(KodeDriveError, self).__init__(
        "%s could not find %s." % (self.application, hostname)
    )

class CannotConnect(KodeDriveError):

  def __init__(self):
    super(KodeDriveError, self).__init__(
    	'Cannot connect to KodeDrive. Is KodeDrive running on this host?'
    )

class PermissionDenied(KodeDriveError):
  def __init__(self):
    super(KodeDriveError, self).__init__(
    	'This folder does not belong to you. Did you add this folder?'
    )

class FileExists(KodeDriveError):
  def __init__(self, f_path):
    super(KodeDriveError, self).__init__(
			"%s already exists." % f_path
    )
