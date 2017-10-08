from setuptools import setup

setup(
    name="pdbox",
    version="0.0.1",
    packages=["pdbox"],
    scripts=["bin/pdbox"],
    install_requires=["appdirs", "dropbox"],
    zip_safe=True,
)
