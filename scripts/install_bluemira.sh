#!/bin/bash

# read -p "Are you in the correct python environment? (y/n) " answer
# case ${answer:0:1} in
#     y|Y )
#         ;;
#     * )
#         exit;;
# esac

# clean_up() {
#   test -d "$tmp_dir" && rm -rf "$tmp_dir"
# }

# tmp_dir=$( mktemp -d -t install-bm.XXX)
# trap "clean_up $tmp_dir" EXIT

# cd $tmp_dir
INSTALL_CONDA=false
PYTHON_VERSION="3.11"
TAG=false
while getopts "i p:t:" flag
do
    case "${flag}" in
        i) INSTALL_CONDA=true;;
        p) PYTHON_VERSION="${OPTARG}";;
        t) TAG="${OPTARG}";;
    esac
done


script_dir=$(dirname "$0")
bluemira_loc=$script_dir"/../bluemira"

if [ ! -d $bluemira_loc ] ; then
    echo
    echo Cloning Bluemira...
    echo
    git clone git@github.com:Fusion-Power-Plant-Framework/bluemira.git $bluemira_loc
    update=false
else
    update=true
    echo Update can only run if no environment is active.
    echo Is an environment activated?
    select strictreply in "Yes/y" "No/n"; do
    relaxedreply=${strictlyreply:-$REPLY}
        case $relaxedreply in
            No | no | n ) echo Continuing update...; break;;
            Yes | yes | y ) echo Please run conda deactivate; exit;;
        esac
    done
    echo
fi

cd $bluemira_loc

if [ "$TAG" = false ] ; then
    echo
    echo Getting latest version:
    latest_tag=$(git describe --tags $(git rev-list --tags --max-count=1))
    echo $latest_tag
    echo
else
    echo
    echo Checking out $TAG
    latest_tag=$TAG
    echo
fi

if [ "$update" = true ] ; then
    echo
    echo Removing old environment...
    echo
    conda remove -n bluemira-bluemira_st --all
    echo
    echo Updating...
    git checkout -q main
    git pull -q
    echo
else
    git checkout -q $latest_tag
    echo
    echo Installing...
    echo
fi

if [ "$INSTALL_CONDA" = true ] ; then
    set -- -e bluemira-bluemira_st -p $PYTHON_VERSION
    OPTIND=1
    source scripts/install-conda.sh
    source ~/.miniforge-init.sh ""
else
    source ~/.miniforge-init.sh ""
    conda env create -f conda/environment.yml -n bluemira-bluemira_st -q
fi

conda activate bluemira-bluemira_st

pip install -e . --config-settings editable_mode=compat
pre-commit install -f

cd ..
pip install -e .
pre-commit install -f

echo
echo Finished
