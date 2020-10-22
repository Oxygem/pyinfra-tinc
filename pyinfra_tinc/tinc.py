import re

from io import BytesIO
from os import path

from pkg_resources import resource_filename

from pyinfra.api import deploy, DeployError
from pyinfra.operations import apt, dnf, files, python, server, systemd, yum

from .defaults import DEFAULTS


def _get_package_filename(*path_components):
    return resource_filename('pyinfra_tinc', path.join(*path_components))


def _get_host_name(host):
    name = host.data.tinc_name or host.name
    return re.sub('[^0-9a-zA-Z]+', '_', name)


def _install_apt_packages(state, host):
    apt.packages(
        name='Install apt packages to compile Tinc',
        packages=['build-essential', 'libssl-dev', 'liblzo2-dev', 'zlib1g-dev'],
        update=True,
        cache_time=3600,
        state=state,
        host=host,
    )


def _install_yum_or_dnf_packages(state, host):
    package_operation = yum.packages
    if host.fact.which('dnf'):
        package_operation = dnf.packages

    package_operation(
        name='Install yum packages to compile Tinc',
        packages=['gcc', 'gcc-c++', 'zlib-devel', 'lzo-devel', 'openssl-devel'],
        state=state,
        host=host,
    )


@deploy('Install Tinc VPN', data_defaults=DEFAULTS)
def install_tinc(state=None, host=None):
    # First, check if Tinc is already installed *and the right version*, noop if so!
    tincd_binary_path = f'{host.data.tinc_install_prefix}/sbin/tincd'
    tinc_version = host.fact.command(f'{tincd_binary_path} --version || true')
    if tinc_version and host.data.tinc_version in tinc_version:
        host.noop(f'Tinc {host.data.tinc_version} is already installed')
        return

    if host.fact.deb_packages:
        _install_apt_packages(state, host)
    elif host.fact.rpm_packages:
        _install_yum_or_dnf_packages(state, host)
    elif not host.data.tinc_ignore_no_package_manager:
        raise DeployError('No RPM or Deb package manage found on this system.')

    temp_filename = state.get_temp_filename(f'tinc-{host.data.tinc_version}')

    files.download(
        name='Download the Tinc source',
        src=f'http://www.tinc-vpn.org/packages/tinc-{host.data.tinc_version}.tar.gz',
        dest=temp_filename,
        state=state,
        host=host,
    )

    server.script_template(
        name='Compile & install Tinc',
        src=_get_package_filename('scripts', 'install_tinc.sh.j2'),
        temp_filename=temp_filename,
        temp_directory=state.config.TEMP_DIR,
        state=state,
        host=host,
    )


@deploy('Configure Tinc VPN', data_defaults=DEFAULTS)
def configure_tinc(netname, network_subnet, host_subnet, host_address, state=None, host=None):
    files.directory(
        name=f'Create the {host.data.tinc_install_prefix}/var/run directory',
        path=f'{host.data.tinc_install_prefix}/var/run',
        state=state,
        host=host,
    )

    config_directory = f'{host.data.tinc_install_prefix}/etc/tinc/{netname}'

    files.directory(
        name='Create the Tinc network config & hosts directories',
        path=f'{config_directory}/hosts',
        state=state,
        host=host,
    )

    files.template(
        name='Generate tinc.conf',
        src=_get_package_filename('templates', 'tinc.conf.j2'),
        dest=f'{config_directory}/tinc.conf',
        get_host_name=_get_host_name,
        state=state,
        host=host,
    )

    files.template(
        name='Generate hosts config',
        src=_get_package_filename('templates', 'tinc-host-base.j2'),
        dest=f'{config_directory}/hosts/{_get_host_name(host)}',
        host_subnet=host_subnet,
        host_address=host_address,
        state=state,
        host=host,
    )

    host_ip = host_subnet.split('/')[0]
    network_mask_bits = network_subnet.split('/')[1]
    host_interface_ip = f'{host_ip}/{network_mask_bits}'

    for script in ('tinc-up', 'tinc-down'):
        files.template(
            name=f'Generate the {script} script',
            src=_get_package_filename('templates', f'{script}.j2'),
            dest=f'{config_directory}/{script}',
            mode=744,
            netname=netname,
            host_interface_ip=host_interface_ip,
            state=state,
            host=host,
        )

    if not host.fact.file(f'{config_directory}/tinc.rsa_key.priv'):
        server.shell(
            name='Generate Tinc key pair',
            commands=[f'{host.data.tinc_install_prefix}/sbin/tincd -n {netname} -K'],
            state=state,
            host=host,
        )

    systemd_unit = files.template(
        name=f'Generate systemd unit tinc-{netname}.service',
        src=_get_package_filename('templates', 'tinc.service.j2'),
        dest=f'/etc/systemd/system/tinc-{netname}.service',
        netname=netname,
        state=state,
        host=host,
    )

    if systemd_unit.changed:
        systemd.daemon_reload(state=state, host=host)


def _sync_tinc_config(state, host, netname, tinc_install_prefix, deploy_kwargs):
    hosts_directory = f'{tinc_install_prefix}/etc/tinc/{netname}/hosts'
    host_filename = f'{hosts_directory}/{_get_host_name(host)}'

    host_config = BytesIO()
    host.get_file(host_filename, host_config)

    # Get the kwargs supplied to the deploy
    deploy_kwargs = deploy_kwargs or {}

    for other_host in state.inventory:
        if host is other_host:
            continue

        other_host.put_file(
            host_config,
            f'{hosts_directory}/{_get_host_name(host)}',
            sudo=deploy_kwargs.get('sudo'),
            sudo_user=deploy_kwargs.get('sudo_user'),
            su_user=deploy_kwargs.get('su_user'),
        )


@deploy('Sync Tinc VPN Configurations', data_defaults=DEFAULTS)
def sync_tinc_configurations(netname, state=None, host=None):
    python.call(
        name='Sync the Tinc config files',
        function=_sync_tinc_config,
        netname=netname,
        tinc_install_prefix=host.data.tinc_install_prefix,
        deploy_kwargs=state.deploy_kwargs,  # will be gone when func executed
        serial=True,  # prevents deadlocking SFTP connection!
        state=state,
        host=host,
    )
