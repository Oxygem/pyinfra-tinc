from io import open

from setuptools import find_packages, setup


with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()


if __name__ == '__main__':
    setup(
        version='0.1',
        name='pyinfra-tinc',
        description='Install & configure the Tinc mesh VPN with `pyinfra`.',
        long_description=readme,
        long_description_content_type='text/markdown',
        url='https://github.com/Oxygem/pyinfra-tinc',
        author='Oxygem Engineers',
        author_email='hello@oxygem.com',
        license='MIT',
        packages=find_packages(),
        python_requires='>=3.6',
        install_requires=('pyinfra~=1.2',),
        include_package_data=True,
    )
