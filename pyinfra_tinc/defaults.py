DEFAULTS = {
    'tinc_version': '1.0.36',
    'tinc_key_length': 2048,
    'tinc_install_prefix': '/usr/local',

    # Don't fail if apt/yum/dnf are not present, instead assume we have the
    # required tooling and attempt to compile Tinc.
    'tinc_ignore_no_package_manager': False,
}
