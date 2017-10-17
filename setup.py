from setuptools import setup, find_packages

setup(
    name="pdbox",
    description="A no-frills CLI for Dropbox",
    author="Chris de Graaf",
    author_email="chrisadegraaf@gmail.com",
    url="https://github.com/christopher-dG/pdbox",
    license="MIT",
    version="0.0.1",
    keywords="terminal cli dropbox",
    packages=find_packages(),
    scripts=["bin/pdbox"],
    install_requires=["appdirs", "boto3", "dropbox", "tabulate"],
    zip_safe=True,
)
