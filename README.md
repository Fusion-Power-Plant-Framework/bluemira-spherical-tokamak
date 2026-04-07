# Bluemira Spherical Tokamak Example

This example build from the PROCESS Spherical Tokamak Regression test

## Usage

To set up your bluemira environment run the following:

```bash
bash scripts/install_bluemira.sh -i
```
If you have already have a conda installation you can remove `-i` and the conda step will be skipped.

Once your bluemira environment is set up run this command everytime you want to activate the environment:

```bash
source ~/.miniforge-init.sh
conda activate bluemira-{{cookiecutter.project_name}}
```

Install PROCESS in your bluemira environment by running the following:
```shell
pip install -e.['process']
```

## Running reactor designs

The example study can be run as shown:

```
python studies/first/reactor.py
```

## Running tests

A test directory is setup (currently empty) once test have been created they can be run with `pytest`.

## Updates

To update to the latest version of bluemira, delete your current environment using:

```
conda env remove -n bluemira-bluemira_st
```

and follow the usage guidelines for installing bluemira and PROCESS.
