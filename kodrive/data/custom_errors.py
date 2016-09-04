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

class InvalidKey(KodeDriveError):

  def __init__(self, key):
    super(KodeDriveError, self).__init__(
      "%s is not a valid key." % key 
    )

class NoFileOrDirectory(KodeDriveError):

  def __init__(self, source, target):
    super(KodeDriveError, self).__init__(
      "mv: rename %s to %s: No such file or directory" % (source, target)
    )

class AlreadyAdded(KodeDriveError):
  def __init__(self):
    super(KodeDriveError, self).__init__(
    	'This folder has already been added.'
    )

class AuthYourself(KodeDriveError):
  def __init__(self):
    super(KodeDriveError, self).__init__(
      'You cannot de/authenticate yourself, please check the key and try again.'
    )

class AuthAlready(KodeDriveError):
  def __init__(self, hostname):
    super(KodeDriveError, self).__init__(
      "%s has already been de/authenticated." % hostname
    )

class NotDirectory(KodeDriveError):
  def __init__(self, f_path):
    super(KodeDriveError, self).__init__(
      "%s is not a directory." % f_path
    )

class StartOnLoginFailure(KodeDriveError):
  def __init__(self):
    super(KodeDriveError, self).__init__(
      "KodeDrive autostart configuration has failed."
    )

