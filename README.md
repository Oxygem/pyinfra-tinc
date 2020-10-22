# `pyinfra` Tinc

A [`pyinfra`](https://github.com/Fizzadar/pyinfra) deploy that installs & configures the [Tinc mesh VPN](https://tinc-vpn.org). Developed & tested with:

+ Ubuntu 18/20
+ Debian 9/10
+ CentOS 7/8

## Usage

A default install and configure of a Tinc network is shown below. Each of the three deploy functions is detailed below.

```py
from pyinfra_tinc import configure_tinc, install_tinc, sync_tinc_configurations

SUDO = True

install_tinc(netname='vpn0')
configure_tinc(netname='vpn0')
sync_tinc_configurations(netname='vpn0')
```

### `install_tinc`

This deploy downloads, compiles & installs the `tincd` binary, along with any required `deb`/`rpm` packages required to do so. This uses the `host.data.tinc_version` variable.

### `configure_tinc`

This deploy generates the Tinc configuration directory and files.

### `sync_tinc_configurations`

This deploy syncs the host configuration files to all other hosts, which actually enables the `tincd` daemons to connect to each other and form the mesh network.
