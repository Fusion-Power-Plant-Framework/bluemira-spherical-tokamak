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

## Running reactor designs

The example study can be run as shown:

```
python studies/first/reactor.py
```

## Running tests

A test directory is setup (currently empty) once test have been created they can be run with `pytest`.
