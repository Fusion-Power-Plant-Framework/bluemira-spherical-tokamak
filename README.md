[![DOI](https://zenodo.org/badge/893984008.svg)](https://zenodo.org/badge/latestdoi/893984008)

# Bluemira Spherical Tokamak Example

This example builds from the PROCESS Spherical Tokamak Regression test

## Usage

To set up your bluemira environment run the following:

```bash
bash scripts/install_bluemira.sh -i
```
If you already have a conda installation you can remove `-i` and the conda step will be skipped.

Once your bluemira environment is set up run this command everytime you want to activate the environment:

```bash
source ~/.miniforge-init.sh
conda activate bluemira-bluemira_st
```

Install PROCESS in your bluemira environment by running the following:
```shell
pip install -e .['process']
```

## Running reactor designs

The example study can be run as shown:

```
python studies/first/reactor.py
```

## Running tests

A test directory is setup (currently empty). Once tests have been created, they can be run with `pytest`.

## Updates

To update to the latest version of bluemira, your bluemira spherical tokamak environment will need to be removed. This is done within the install script, but requires that you are not currently in an activated environment. You can deactivate your environment by running:

```bash
conda deactivate
```

Then run the install script to complete the update:

```bash
bash scripts/install_bluemira.sh
```
