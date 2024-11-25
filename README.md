# Bluemira template-project

---

## Setting up and using this template

Start by git cloning this repository (or use the "Use this template" button on GitHub).

```bash
git clone git@github.com:Fusion-Power-Plant-Framework/bluemira-template-project.git my_bm_project
cd my_bm_project
```
We use the [cookiecutter](https://github.com/cookiecutter/cookiecutter) project to setup a new bluemira project.

With your local copy of the repository run the following script and fill in the prompts with the details. You will need pip available to install cookiecutter.

```bash
bash scripts/setup_repo.sh
```

You can then add and commit the resulting changes.

Finally to set up your bluemira environment run the following, until bluemira >v2.4.0 you will need to use the develop branch to use this template:

```bash
bash scripts/install_bluemira.sh -i -t develop
```

If you have already have a conda installation you can remove `-i` and the conda step will be skipped. Once the environment is setup please activate your environment replacing `{your_project_name}` with the appropriate value:

```bash
source ~/.miniforge-init.sh
conda activate bluemira-{your_project_name}
```

Any suggested improvements to the setup experience is welcomed, please open an issue or even better a PR!

## Running reactor designs

The example study can be run as shown once the setup has been completed:

```
python studies/first/run.py
```

## Running tests

A test directory is setup (currently empty) once test have been created they can be run with `pytest`.

Once set up this repo creates a github action to run the tests against the current bluemira develop branch which runs on a cron job schedule. By default this runs twice a day.
