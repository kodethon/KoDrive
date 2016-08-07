# KodeDrive

Synchronize remote files and directories across different devices with an easy-to-use CLI.

## Getting Started

### Install Dependencies
To use KodeDrive, the following must be installed:

- [Python 2.7](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installing/)
```sh
$ curl https://bootstrap.pypa.io/get-pip.py | python
```
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)


### Install KodeDrive
To set ```kdr``` (the KodeDrive CLI) as a local command:

    $ pip install --user virtualenv
    $ curl https://raw.githubusercontent.com/Jvlythical/KodeDrive/master/static/get-kdr.py | python
    
or to set ```kdr``` as a global command (```sudo``` permission is required):

    $ pip install virtualenv
    $ curl https://raw.githubusercontent.com/Jvlythical/KodeDrive/master/static/get-kdr-global.py | python

### Initialize the KodeDrive Daemon

```sh
$ kdr sys -i
```

## Linking Directories

1. Provide the other person with your **device key**:

  ```sh
  $ kdr sys -k
  ```
2. The person sharing with you will then provide a **folder key**:

  ```sh
  $ kdr link <FOLDER-KEY>
  ```

## Sharing Directories

1. A folder must first be **added** before it can be shared:   

  ```sh
  $ kdr add <PATH>
  ```
2. Next the folder needs to be **authorized** with another user's device key:   

  ```sh
  $ kdr auth -a <DEVICE-KEY> <PATH>
  ```
3. Finally obtain and provide the below **folder key** back to the other user:
 
  ```sh
  $ kdr key <PATH>
  ```
Below is an illustration of the above process:
<p align="center">
  <img src="https://github.com/Jvlythical/KodeDrive/blob/master/static/images/client-client-circle.png" alt="Client-Client"/>
</p>

## Linking/Sharing Directories Detailed
_**Note**: 'Sharer' refers to the device that is sharing their directory and 'receiver' refers to the device that the 'sharer' is sharing their directory with._


First, the receiver(s) need to supply their device key(s) to the sharer with:
```sh
$ kdr sys -k
```

The sharer then:

1. Adds the directory to be shared with ```kdr add <PATH>```
  ```sh
  $ kdr add <PATH>
  $ kdr ls
  ```

  * _**Note**: ```kdr ls``` is optional and can be used before and/or after adding and freeing directories to verify._
2. Authorizes a receiver to that directory (```-a``` stands for ```--add```).
  ```sh
  $ kdr auth -a <RECEIVER_DEVICE_KEY> <PATH>
  $ kdr auth -l
  ```

  * _**Note**: ```kdr auth -l``` is optional and can be used before and after de/authorizing devices to see who has access to which directories._
3. Gets the key which the receiver will need to link.

  ```sh
  $ kdr key <PATH>
  ```

Running ```kdr key <PATH>``` will return the directory's key, which needs to be passed to the receiver(s).

_**Note**: When there are multiple receivers, the sharer will need to authorize each receiver and supply them with the key._


The receiver(s) then link to the sharer **in the directory** where they would like to save the files:

_**CAUTION**: linking will merge the 2 directories so that the sharer and receiver will have access to **everything in BOTH** directories. This can lead to the sharing of sensitive data as well as conflicts if there are files with the same name. It is recommended for a receiver to link while in an empty directory. See [conflicts](https://github.com/Jvlythical/KodeDrive#conflicts) for more information._

```sh
$ kdr link <DIRECTORY_KEY>
```

Now the authorized devices have access to the directory and can add, modify and remove files. KodeDrive is configured so that the daemon scans the directory for changes every 30 seconds.

To force a rescan and sync the directory immediately:
```sh
$ kdr push <PATH>
```

## Stopping Synchronization
The sharer can deauthorize access to certain users:

1. ```kdr auth -l``` lists all directories authorized to others and the devices which are authorized. This can be useful for ```kdr auth -a/-r``` to obtain device keys and verify whether a device has been deauthorized.

2. ```kdr auth -r <RECEIVER_DEVICE_ID> <PATH>``` deauthorizes a certain receiver to a directory. (```-r``` for ```--remove```) 

```sh
$ kdr auth -l
$ kdr auth -r <RECEIVER_DEVICE_ID> <PATH>
```

Furthermore, the sharer can completely remove the directory from the daemon which will deauthorize all devices to that directory:
```sh
$ kdr free <PATH>
```

The receiver(s) can only ```kdr free <PATH>``` since it is not their directory. They are not allowed to ```kdr auth -a/-r``` since they are not the sharer:
```sh
$ kdr free <PATH>
```


## Advanced Usage

### Server Mode

By default, all daemons are in client mode.
For normal use cases, use **_Client-Client_** synchronization described above. Server mode can be advantageous for quick sharing and syncing from a single device such as a secure server, but can be dangerous if misused. Note that **_Server-Client_** connections will not work if the device in Server mode does not allow direct or open connections.

_**CAUTION**: **Server-Client** connections can be unsecure and can lead to potential security risks if used improperly._

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

Below is an illustration of the above process:
<p align="center">
  <img src="https://github.com/Jvlythical/KodeDrive/blob/master/static/images/server-client.png" alt="Server-Client"/>
</p>

#### Stopping Synchronization as Server-Client
For both the sharer and the receivers:
```sh
$ kdr free <PATH>
```

### Conflicts

If a file is modified on different devices simultaneously or files with the same name in different directories are synchronized, the file on the device with the larger value of the first 63 bits for their device ID will be marked as the conflicting file. The file will be renamed to ```<filename>.sync- conflict-<date>-<time>.<ext>```

It will be up to the users to resolve conflicts and update their files in this case.

Please note that if users modify conflict files, it is possible to end up with conflicting conflict files.
Those will be named as ```sync-conflict-...sync-conflict -...-sync-conflict``` files.
