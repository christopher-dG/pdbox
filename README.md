# pdbox

**A no-frills CLI for Dropbox modelled after AWS's S3 interface.**

## Installation

With `pip`:

```
$ pip install git+https://github.com/christopher-dG/pdbox
```

Or from source:

```
$ git clone https://github.com/christopher-dG/pdbox
$ cd pdbox
$ python setup.py install
```

## Usage

```
usage: pdbox [-h] {cp,ls,mb,mv,rb,rm,sync} ...

positional arguments:
  {cp,ls,mb,mv,rb,rm,sync}
    cp                  copy file to/from/inside Dropbox
    ls                  list a folder inside Dropbox
    mb                  create a new folder inside Dropbox
    mv                  move a file or object inside Dropbox
    rb                  delete a folder inside Dropbox
    rm                  delete a file or directory inside Dropbox
    sync                copy file to/from/inside Dropbox

optional arguments:
  -h, --help            show this help message and exit
```

## Access Tokens

To access Dropbox, an OAuth2 access token is required. `pdbox` will take care
of this for you, but if you already have a token and want to use it, you can
set the `PDBOX_TOKEN` environment variable.

## Motivation

> Dropbox already has a CLI, what's the point?

Installing `dropbox-cli` on Arch Linux uses 147 MB, that's a lot!
This is not intended for "power users" looking for advanced sync
functionality and more, but rather for those looking for a quick, easy way to
access their files when the full Dropbox client isn't practical, such as
headless VMs or low-resource servers.

## Python 2

This code is compatible with both Python 2 and 3 but
[this bug with the Dropbox SDK](https://github.com/dropbox/dropbox-sdk-python/issues/85)
may affect you, in which case I recommend that you use Python 3.
