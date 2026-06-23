from setuptools import find_packages, setup

install_requires = [
    "acme>=2.11.0",
    "certbot>=2.11.0",
    "certifi==2024.8.30",
    "cffi==1.17.0",
    "charset-normalizer==3.3.2",
    "ConfigArgParse==1.7",
    "configobj==5.0.8",
    "cryptography>=3.2.1",
    "distro==1.9.0",
    "idna==3.8",
    "parsedatetime==2.6",
    "pycparser==2.22",
    "PyOpenSSL>=25.0.0",
    "pyRFC3339==1.1",
    "pytz==2024.1",
    "requests==2.32.3",
    "ruff==0.6.3",
    "setuptools==74.0.0",
    "six==1.16.0",
    "urllib3==2.2.2",
    "wheel==0.44.0",
]

VERSION = "0.0.9"

DESCRIPTION = "Certbot DNS plugin for mijn.host service, enabling the automation of DNS-01 challenges for issuing wildcard SSL certificates. This plugin simplifies the process of obtaining and renewing SSL certificates by integrating directly with the DNS API of mijn.host Service, making it ideal for system administrators and DevOps professionals managing secure web services."

with open("README.md", "r", encoding="utf-8") as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name="certbot-dns-mijn-host",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/certbot-dns-mijn-host/",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "certbot.plugins": [
            "dns-mijn-host = certbot_dns_mijn_host.mijn_host:Authenticator"
        ]
    },
)
