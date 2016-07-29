# KodeDrive

Synchronize remote files and directories across different devices and users with an easy-to-use CLI.

## Installation

Copy and paste:

    $ curl https://raw.githubusercontent.com/Jvlythical/KodeDrive/master/static/get-kdr.py | python


## Getting Started

To see all of the commands:

    $ kdr --help
    
### Initializing the KodeDrive Daemon
```sh
$ kdr sys -i
```

## Synchronizing Files and Directories
_**Note**: 'Sharer' refers to the device that is sharing their directory and 'receiver' refers to the device that the 'sharer' is sharing their directory with._


First, the receiver(s) need to supply their device key(s) to the sharer with:
```sh
$ kdr sys -k
```

The sharer then adds the directory to be shared and authorizes the receiver:
```sh
$ kdr add <PATH>
$ kdr auth -a <PATH> <RECEIVER_DEVICE_KEY>
$ kdr key <PATH>
```

Running ```kdr key <PATH>``` will return the directory's key, which needs to be passed to the receiver(s).

The receiver(s) then links to the sharer:
```sh
$ kdr link <DIRECTORY_KEY>
```
in the directory where they would like to save the data.

## Stopping Synchronization
The sharer can deauthorize access to certain users:
```sh
$ kdr auth -l
$ kdr auth -r <PATH> <RECEIVER_DEVICE_ID>
```

```kdr auth -l``` lists all directories authorized to others in the form of their device keys.

```kdr auth -r ...``` removed authorization of a directory to a certain receiver.


.. and/or completely remove the directory from the daemon which will deauthorize all receivers:
```sh
$ kdr free <PATH>
```

```kdr free ...``` will completely remove the directory from the daemon.

The receiver can only ```kdr free ...``` since it is not their directory:
```sh
$ kdr free <PATH>
```


## Advanced Usage

### Server Mode

By default, all daemons are in client mode.
For normal use cases, use **_Client-Client_** synchronization described above. **_Server-Client_** connections will not work if the device in Server mode does not allow direct or open connections.

To switch into server mode:
```sh
$ kdr sys -s
```

To switch back into client mode:
```sh
$ kdr sys -c
```

To see the KodeDrive status and which mode it is currently in:
```sh
$ kdr sys -a
```

#### Synchronizing as Server-Client

The server (in Server mode) does:
```sh
$ kdr add <PATH>
$ kdr key <PATH>
```

The client(s) (in Client mode) run:
```sh
$ kdr link <KEY>
```
with the key given by the server.

#### Stopping Synchronization as Server-Client
For both the sharer and the receivers:
```sh
$ kdr free <PATH>
```

### Conflicts

If a file is modified on different devices simultaneously, the file on the device with the larger value of the first 63 bits for their device ID will be marked as the conflicting file. The file will be renamed to ```<filename>.sync- conflict-<date>-<time>.<ext>```

It will be up to the users to resolve conflicts and update their files in this case.

Please note that if users modify conflict files, it is possible to end up with conflicting conflict files.
Those will be named as ```sync-conflict-...sync-conflict -...-sync-conflict``` files.

Refer to Syncthing's [FAQ](https://docs.syncthing.net/users/faq.html?highlight=conflicts).

## Dependencies
- Python 2.7
- [virtualenv](https://github.com/pypa/virtualenv)