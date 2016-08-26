import os

class PList:
  def __init__(self, plist_name, HOME, bin_binary):

    self.file = {
      'Label': plist_name,

      'ProgramArguments': [
        bin_binary, '-no-browser',
        '-logfile', os.path.join(HOME, 'Library/Application Support/Syncthing/log'),
        '-home', os.path.join(HOME, 'Library/Application Support/Syncthing'),
        '-gui-address', '127.0.0.1:8384'
      ],

      'EnvironmentVariables': {
        'HOME': HOME,
        'STNOUPGRADE' : '1'#,
        # 'STNORESTART' : '1'
      },

      'KeepAlive': {
        'SuccessfulExit': False
      },

      'RunAtLoad': True,
      'ProcessType': 'Interactive',
      'StandardOutPath': os.path.join(HOME, 'Library/Application Support/Syncthing/log'), 
      'StandardErrorPath': os.path.join(HOME, 'Library/Application Support/Syncthing/log')
    }

  @property
  def obj(self):
    return self.file
