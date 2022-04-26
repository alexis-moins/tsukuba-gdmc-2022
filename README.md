# Tsukuba GDMC 2022

This repository is an entry for the annual GDMC competition of 2022.

## How to use ?

### Clone the repository

Start by cloning the repository to get the files on your machine. Alternatively, you can change `~/GDMC` to any location you want.

```bash
# Get the files on your computer
git clone git@github.com:AlexisMoins/tsukuba-gdmc-2022.git ~/GDMC
```

### Setup the environment

**Note:** This repository relies on multiple python packages. You can find out which ones are used in the `pyprojet.toml` file. To manage our packages, We used [poetry](https://python-poetry.org). If you are not using this tool, you should try to install the packages directly via `pip`.  

As a final note, please notice that the syntax used across the projet is python version **3.10** so you might want to install version 3.10 via python's [official website](https://www.python.org) or via tools like [pyenv](https://github.com/pyenv/pyenv).

```bash
# First, enter the directory
cd ~/GDMC

# Install packages and start virtual env
poetry install && poetry shell
```

Using `pip`, the main packages that you should install are `gdpc`, `pytest` if you want to run tests, `pre-commit` to keep the requirements.txt file **synchronized**. Exact versions of the aforementioned packages can again be found in the `pyproject.toml` file. Alternatively, you can directly install the dependencies by typing :

```bash
# Install packages using pip
pip install -r requirements.txt
```

### Adding pre-commit hooks

To keep the `requirements.txt` file in sync with the `pyproject.toml` file (given that the `pre-commit` package is installed), you need to run the following command :

```bash
pre-commit install
```

### Launch the simulation

Once the environment is ready, simply launch the main script and you're good to go !

```bash
python main.py
```
