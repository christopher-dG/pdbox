# pdbox

[![Build Status](https://travis-ci.org/christopher-dG/pdbox.svg?branch=master)](https://travis-ci.org/christopher-dG/pdbox)
[![Project Status](http://www.repostatus.org/badges/latest/wip.svg)](http://www.repostatus.org/#wip)

**A no-frills CLI for Dropbox.**

## Pre-Release Note

This software is a work in progress. I make no guarantees about its
correctness, and will take no responsibility for any data loss that may occur
(although I will apologize profusely).

## Installation

With `pip`:

```
$ pip install git+https://github.com/christopher-dG/pdbox
```

From source:

```
$ git clone https://github.com/christopher-dG/pdbox
$ cd pdbox
$ python setup.py install
```

## Usage

```
usage: pdbox [-h] [-d] {ls,cp,mv,mkdir,rm,rmdir,tui} ...

positional arguments:
  {ls,cp,mv,mkdir,rm,rmdir,tui}
    ls                  list folders
    cp                  copy files
    mv                  move files or folders
    mkdir               create folders
    rm                  delete files or folders
    rmdir               delete folders
    tui                 run pdbox in an interactive TUI

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           show debug messages
```

## Motivation

> Dropbox already has a CLI, what's the point?

Installing `dropbox-cli` on Arch Linux uses 147 MB, that's a lot!  
This is not intended for "power users" looking for advanced sync
functionality and more, but rather for those looking for a quick, easy way to
access their files when the full Dropbox client isn't practical, such as
headless VMs or low-resource servers (or CLI addicts like me).

Update: I was not aware of [dbxcli](https://github.com/dropbox/dbxcli) at the
time of writing, this is awkward...

## Python 2

This code is compatible with both Python 2 and 3 but
[this bug with the Dropbox SDK](https://github.com/dropbox/dropbox-sdk-python/issues/85)
may affect you, in which case I recommend that you use Python 3.

## TODO

* Much better test coverage
* A smart folder sync command
* A TUI (finally something you don't get with dbxcli!)
