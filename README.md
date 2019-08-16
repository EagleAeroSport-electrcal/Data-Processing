# Data Processing

Repository for data processing code for EAS

## Table Of Contents

- [Data Processing](#data-processing)
  - [Table Of Contents](#table-of-contents)
  - [Contributing](#contributing)
    - [Setup](#setup)
      - [Python Version](#python-version)
      - [Virtual Environment](#virtual-environment)
      - [Requirements File](#requirements-file)
    - [Submissions](#submissions)
  - [Development Environments](#development-environments)

## Contributing

### Setup

#### Python Version

Python version 3.6 or newer is **required** due to variable type hints being used.
Python 3.7 is recommended as that is the version that the program has been tested on.

#### Virtual Environment

To contribute to this project, it is recommended to set up a python virtual environment using [venv](https://docs.python.org/3/library/venv.html).
Initializate a virtual enviroment with `python -m venv .venv`.\
When launching a terminal session to use with the project, activate the session using

- `.venv/Scripts/activate` for Windows command line
- `.venv/Scripts/activate.ps1` for PowerShell
- `source .venv/bin/activate` for Unix

#### Requirements File

All necessary python requirements for the program, as well as linters, are specified in the file `requirements.txt`. To install them all, use the command `python -m pip install -U -r requirements.txt`.\
Using -U ensures that the correct version will be inststalled, even if a different version is already installed.
If not necessary, the requirements do not have a specific version set in the file, to allow for automatic installation of the newest version of the program.

### Submissions

To submit modifications to this project, use the standard GitHub pull request system.\
Prior to filing a pull request, the following steps must be performed:

- Program does not fail the `pycodestyle` and `pydocstyle` linters
- Program does not fail `flake8` with all plugins specified in `requirements.txt` installed
- Program does not fail any unit tests.
- New features has corresponding unit tests

Note that in the near future, all of this will be automatically tested on creation of a Pull Request, and Pull Request acceptance will be dependent on the results. A fail of one or more of the above does not guarentee a rejection of the Pull Request, as false positives do happen.

## Development Environments

A .vscode folder is pre-configured with the project. It contains all of the settings and build tasks to allow the project to be directly loaded into Visual Studio Code and leverage all of its features.\
Feel free to add other configuration folders leveraging whatever IDE you choose to use, but make sure that project level settings **only** contain settings related to the project, and not user preferences such as themes and keyboard shortcuts.
