import importlib_resources
import logging
from os import environ, listdir, mkdir, path
import subprocess

home_folder = environ["HOME"]

# Install Ingenii quantum package in startup folder
startup_folder = home_folder + "/.ipython/profile_default/startup"
for file in listdir(startup_folder):
    if not (file.endswith(".whl") and file.startswith("ingenii_azure_quantum")):
        continue

    res = subprocess.run(
        f"pip install {startup_folder}/{file}".split(" "),
        capture_output=True
    )
    logging.info(res.stdout)
    if res.returncode != 0:
        raise Exception(res.stderr)

examples_folder_name = "quantum_examples"
examples_folder = f"{home_folder}/{examples_folder_name}"

# Check if we need to create the 'quantum_examples' folder
folder_exists = any(
    folder == examples_folder_name
    for folder in listdir(home_folder)
    if path.isdir(f"{home_folder}/{folder}")
)
if not folder_exists:
    mkdir(examples_folder)

# Check each file in the examples folder
for example in importlib_resources.files("ingenii_azure_quantum.examples").iterdir():
    if not (example.name.endswith(".py") or example.name.endswith(".ipynb")):
        continue

    new_file = f"{examples_folder}/{example.name}"

    # Don't overwrite the file if it already exists
    if path.exists(new_file):
        continue

    with open(new_file, "w") as example_file:
        example_file.write(example.open().read())
