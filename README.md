# KodeDrive

[![PyPI](https://img.shields.io/pypi/status/Django.svg?maxAge=2592000)](https://pypi.python.org/pypi/kdr/0.9.86)
[![PyPI](https://img.shields.io/badge/pypi-v0.9.86-blue.svg)](https://pypi.python.org/pypi/kdr/0.9.86)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Synchronize remote files and directories across different devices with an easy-to-use CLI.

## Getting Started

### Install Dependencies
To use KodeDrive, the following must be installed:

- Python 2.7
- pip
- virtualenv

Refer to the [Dependencies](#dependencies) section.

### Install KodeDrive
To set ```kdr``` (the KodeDrive CLI) as a local command:

    $ curl https://raw.githubusercontent.com/Jvlythical/KodeDrive/master/static/get-kdr.py | python

### Initialize the KodeDrive Daemon

```sh
$ kdr sys -i
```

## Receiving Directories

1. Provide the other person with your **device key**:

  ```sh
  $ kdr key -d
  ```
2. The person sharing with you will then provide a **directory key**:

  ```sh
  $ kdr link <DIRECTORY-KEY>
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
3. Finally obtain and provide the below **directory key** back to the other user:
 
  ```sh
  $ kdr key -f <PATH>
  ```
  
<p align="center">
  <img src="https://github.com/Jvlythical/KodeDrive/blob/master/static/images/client-client-circle.png" alt="Client-Client"/>
</p>
<p align="center">
    <b>Figure 1.</b> An illustration of the above process.
</p>

## Receiving/Sharing Directories in Detail
_**CAUTION**: If you decide to skip this section, please continue on to the Conflicts section._

_**Note**: 'Sharer' refers to the device that is sharing their directory and 'receiver' refers to the device that the 'sharer' is sharing their directory with._

First, the receiver(s) need to supply their device key(s) to the sharer with:
```sh
$ kdr key -d 
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
  $ kdr auth -a <RECEIVER-DEVICE-KEY> <PATH>
  $ kdr auth -l
  ```

  * _**Note**: ```kdr auth -l``` is optional and can be used before and after de/authorizing devices to see who has access to which directories._
3. Gets the key which the receiver will need to link.

  ```sh
  $ kdr key -f <PATH>
  ```

Running ```kdr key <PATH>``` will return the directory's key, which needs to be passed to the receiver(s).

_**Note**: When there are multiple receivers, the sharer will need to authorize each receiver and supply them with the key._


The receiver(s) then link to the sharer **in the directory** where they would like to save the files:

_**CAUTION**: linking will merge the 2 directories so that the sharer and receiver will have access to **everything in BOTH** directories. This can lead to the sharing of sensitive data as well as conflicts if there are files with the same name. It is recommended for a receiver to link while in an empty directory. See [conflicts](https://github.com/Jvlythical/KodeDrive#conflicts) for more information._

```sh
$ kdr link <DIRECTORY-KEY>
```

Now the authorized devices have access to the directory and can add, modify and remove files. KodeDrive is configured so that the daemon scans the directory for changes every 30 seconds.

To force a rescan and sync the directory immediately:
```sh
$ kdr push <PATH>
```

## Stopping Synchronization
The sharer can deauthorize access to certain users:

1. ```kdr auth -l``` lists all directories authorized to others and the devices which are authorized. This can be useful for ```kdr auth -a/-r``` to obtain device keys and verify whether a device has been deauthorized.

2. ```kdr auth -r <RECEIVER-DEVICE-ID> <PATH>``` deauthorizes a certain receiver to a directory. (```-r``` for ```--remove```) 

```sh
$ kdr auth -l
$ kdr auth -r <RECEIVER-DEVICE-ID> <PATH>
```

Furthermore, the sharer can completely remove the directory from the daemon which will deauthorize all devices from that directory:
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
$ kdr info -d
```

#### Synchronizing as Server-Client

The server (in Server mode) does:
```sh
$ kdr add <PATH>
$ kdr key -f <PATH>
```

The client(s) (in Client mode) run:
```sh
$ kdr link <KEY>
```
with the key given by the server.

<p align="center">
  <img src="https://github.com/Jvlythical/KodeDrive/blob/master/static/images/server-client.png" alt="Server-Client"/>
</p>
<p align="center">
    <b>Figure 2.</b> An illustration of the above process.
</p>

#### Stopping Synchronization as Server-Client
For both the sharer and the receivers:
```sh
$ kdr free <PATH>
```

### Statistics
To see statistics on a directory currently being synchronized:
```sh
$ kdr info -f <PATH>
```

### Changing the Rescan Interval
By default, KodeDrive scans each directory every 30 seconds for changes and propagates those changes to all linked directories. Decreasing the interval can lead to faster syncing, but will make KodeDrive more CPU and memory intensive and vice versa. This can be problematic if syncing large directories/files on slower computers and it is advised to seek a balance.

Note: this will only change the interval on the device running this command and will restart KodeDrive.

### Conflicts

_**CAUTION**: KodeDrive will not automatically start when your computer boots up, please start KodeDrive to avoid potential conflicts._

If a file is modified on different devices simultaneously or files with the same name in different directories are synchronized, the file on the device with the larger value of the first 63 bits for their device ID will be marked as the conflicting file. The file will be renamed to ```<filename>.sync- conflict-<date>-<time>.<ext>```

It will be up to the users to resolve conflicts and update files. It is advised to avoid conflicts if possible.

Please note that if users modify conflict files, it is possible to end up with conflicting conflict files.
Those will be named as ```sync-conflict-...sync-conflict -...-sync-conflict``` files.

## Dependencies
- [Python 2.7](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installing/)
```sh
$ curl https://bootstrap.pypa.io/get-pip.py | sudo python
```
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
```sh
$ pip install --user virtualenv
```

