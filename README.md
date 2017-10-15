# pdbox

[![Build Status](https://travis-ci.org/christopher-dG/pdbox.svg?branch=master)](https://travis-ci.org/christopher-dG/pdbox)
[![Project Status](http://www.repostatus.org/badges/latest/wip.svg)](http://www.repostatus.org/#wip)

**A no-frills CLI for Dropbox inspired by
[AWS's S3 interface](http://docs.aws.amazon.com/cli/latest/reference/s3/index.html).**

## Pre-Release Note

Secure handling of the app secret isn't yet implemented. For now, you'll need
to [create your own app](https://www.dropbox.com/developers/apps/create) with
full Dropbox access and store its credentials in `$PDBOX_KEY` and
`$PDBOX_SECRET` environment variables if you wish to use this.

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
usage: pdbox [-h] [-d] {cp,ls,mb,mv,rb,rm,sync} ...

positional arguments:
  {cp,ls,mb,mv,rb,rm,sync}
    cp                  copy a file to/from/inside Dropbox
    ls                  list a folder inside Dropbox
    mb                  create a new folder inside Dropbox
    mv                  move a file or object inside Dropbox
    rb                  delete a folder inside Dropbox
    rm                  delete a file or directory inside Dropbox
    sync                synchronize a folder to/from/inside Dropbox

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           show debug messages
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
