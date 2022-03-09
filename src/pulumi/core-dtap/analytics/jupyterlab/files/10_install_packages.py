import logging
from os import environ, getcwd, listdir
import subprocess

def install_package(package, *args):
    res = subprocess.run(
        f"pip install {package}".split(" ") + [*args],
        capture_output=True
    )
    logging.info(res.stdout)
    if res.returncode != 0:
        raise Exception(res.stderr)

install_package("azure-cli")

# Install all packages in startup folder
folder = environ["HOME"] + "/.ipython/profile_default/startup"
for file in listdir(folder):
    if not file.endswith(".whl"):
        continue

    install_package(f"{folder}/{file}")
