from pyinfra import host
from pyinfra.operations import server

from pyinfra_tinc import configure_tinc, install_tinc, sync_tinc_configurations

SUDO = True


tinc_netname = 'vpn0'
tinc_network_subnet = '10.22.42.0/24'

# Normally you'd define this inside the inventory for each host!
tinc_host_ips = {
    '@vagrant/ubuntu18': '10.22.42.1',
    '@vagrant/ubuntu20': '10.22.42.2',
    '@vagrant/debian9': '10.22.42.3',
    '@vagrant/debian10': '10.22.42.4',
    '@vagrant/centos7': '10.22.42.5',
    '@vagrant/centos8': '10.22.42.6',
}

# Compile & install the Tinc daemon
install_tinc()

# Configure the Tinc network
configure_tinc(
    netname=tinc_netname,
    network_subnet=tinc_network_subnet,
    host_subnet=tinc_host_ips[host.name],
    host_address=host.fact.ipv4_addresses['eth1'],
)

# Sync the configuration files between every host
sync_tinc_configurations(netname=tinc_netname)

# Finally, start or restart Tinc
server.service(
    name='Restart the Tinc service',
    service=f'tinc-{tinc_netname}',
    running=True,
    restarted=True,
)
