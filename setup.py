from setuptools import find_packages, setup

install_requires = [
    "certbot>=2.11.0",
    "requests>=2.20.0",
]

VERSION = "0.0.10"

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
