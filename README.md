# pdbox

**A no-frills CLI for Dropbox.**

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
usage: pdbox [-h] [-y] [-f] <command> <filename> [destination]

positional arguments:
  <command>    'get' or 'put'
  <filename>   file to get or put
  destination  where to put the file (optional)

optional arguments:
  -h, --help   show this help message and exit
  -y, --yes    don't prompt for confirmation
  -f, --force  overwrite existing files
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
