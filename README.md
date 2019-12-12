# PyBaMM results

This repository provides a template for generating results (for example, for a paper) using [PyBaMM](https://github.com/pybamm-team/PyBaMM)

## Installation

1. Install PyBaMM using a virtual environment
1. Activate PyBaMM's virtual environment

If you want to create the repository once and then forget about it, you can specify a particular PyBaMM version number or commit hash that the repository works with. Alternatively, you can set up Travis-CI to notify you if any changes to PyBaMM cause your repository to break, to make sure that your repository stays up to date with the latest improvements in PyBaMM

## Making your own repository

1. Make a new repository in your own GitHub account
1. Copy the contents of this repository into this new repository
1. In your copy, edit this README with information about your own paper
1. In your copy, replace files in the `results` folder with files that generate the plots in your paper
1. Either:
    - Set up [Travis-CI]() to run tests to make sure that your repository works with the latest version of PyBaMM
or:
    - Specify the PyBaMM version number or commit hash with which your repository works

## Repositories that use PyBaMM

The following repositories already use PyBaMM and can be explored as examples additional to the ones provided within the PyBaMM repository:

If you want to add your repository to this list, [open an issue](https://github.com/pybamm-team/cookie-cutter-results/issues/new)!
