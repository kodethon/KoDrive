# KoDrive

[![Build](https://img.shields.io/travis/Jvlythical/KoDrive/master.svg)](https://travis-ci.org/Jvlythical/KoDrive)
[![PyPI](https://img.shields.io/pypi/v/kodrive.svg)](https://pypi.python.org/pypi/kodrive)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Synchronize remote files and directories across different devices with an easy-to-use CLI.

![](static/videos/demo.gif)

## Getting Started

### Install Dependencies

- [Python 2.7](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installing/)
```sh
$ curl https://bootstrap.pypa.io/get-pip.py | sudo python
```
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
```sh
$ pip install --user virtualenv
```

### Install KoDrive
To set ```kodrive``` as a local command:

    $ curl https://raw.githubusercontent.com/Jvlythical/KoDrive/master/static/get-kodrive.py | python

### Initialize the KoDrive Daemon

```sh
$ kodrive sys start
```

## Receive Directories

1. Provide the other person with your **system key**:

  ```sh
  $ kodrive sys key 
  ```
2. The person sharing their directory will then provide a **directory key** to link with:

  _**CAUTION**: linking will merge the 2 directories and grant access to **everything in BOTH** directories. This can lead to the sharing of sensitive data as well as conflicts. It is recommended for a receiver to link while in an empty directory. See [conflicts](https://github.com/Jvlythical/KoDrive#conflicts) for more information._

  ```sh
  $ kodrive link <DIRECTORY-KEY>
  ```

## Share Directories

1. The other user needs to be authorized (via their **system key**) to receive the directory:   

  ```sh
  $ kodrive auth <SYSTEM-KEY> 
  ```
2. Then obtain and provide the below **directory key** back to the other user:
 
  ```sh
  $ kodrive dir key <PATH>
  ```
  
<p align="center">
  <img src="https://github.com/Jvlythical/KoDrive/blob/master/static/images/client-client-circle.png" alt="Client-Client"/>
</p>
<p align="center">
    <b>Figure 1.</b> An illustration of the above process.
</p>


## Stop Synchronization

# Receive Directories

The receiver(s) can only ```kodrive dir free <PATH>``` since it is not their directory:
```sh
$ kodrive dir free <PATH>
```

# Share Directories

The sharer can deauthorize access to certain users since they own the directory:

<!-- 1. ```kodrive auth -l``` lists all directories authorized to others and the devices which are authorized. This can be useful for ```kodrive dir auth -a/-r``` to obtain system keys and verify whether a device has been deauthorized. -->

<!-- 2. ```kodrive auth -R <RECEIVER-SYSTEM-KEY> <PATH>``` deauthorizes a certain receiver from a directory. (```-R``` for ```--remove```)  -->
```kodrive auth -R <RECEIVER-SYSTEM-KEY> --path <PATH>``` deauthorizes a certain receiver from a directory. (```-R``` for ```--remove```) 

<!-- $ kodrive dir auth -l -->

<!-- ```sh -->
<!-- $ kodrive dir auth -R <RECEIVER-SYSTEM-KEY> --path <PATH> -->
<!-- ``` -->

Furthermore, the sharer can completely remove the directory from the daemon which will deauthorize all devices from that directory:
```sh
$ kodrive dir free <PATH>
```
