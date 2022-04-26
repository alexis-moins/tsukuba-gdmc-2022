# Tsukuba GDMC 2022

This repository is an entry for the annual GDMC competition of 2022.

## How to use

### Clone the repository

Start by cloning the repository to get the files on your machine. Alternatively, you can change `~/GDMC` to any location you want.

```bash
git clone git@github.com:AlexisMoins/tsukuba-gdmc-2022.git ~/GDMC && cd ~/GDMC
```

### Setup the environment

**Note:** This repository relies on multiple python packages. You can find out which ones are used in the `pyprojet.toml` file. To manage our packages, We used [poetry](https://python-poetry.org). If you are not using this tool, you should try to install the packages directly via `pip`.  

As a final note, please notice that the syntax used across the projet is python version **3.10** so you might want to install version 3.10 via python's [official website](https://www.python.org) or via tools like [pyenv](https://github.com/pyenv/pyenv).

This command will install the dependencies and start a new virtual environment

```bash
poetry install && poetry shell
```

Using `pip`, the main packages that you should install are `gdpc`, `pytest` if you want to run tests, `pre-commit` to keep the requirements.txt file **synchronized**. Exact versions of the aforementioned packages can again be found in the `pyproject.toml` file. Alternatively, you can directly install the dependencies by typing :

```bash
pip install -r requirements.txt
```

### Add pre-commit hooks (optional)

To keep the `requirements.txt` file in sync with the `pyproject.toml` file (given that the `pre-commit` package is installed), you need to run one of the following commands.

If you have launched a poetry virtual env:

```bash
pre-commit install
```

Otherwise, use one of the following (depending on your case)
- if you use poetry :

  ```bash
  poetry run pre-commit install
  ```
 
- or, if you use pip: 

  ```bash
  python -m pre-commit install
  ```


### Install the GDPC Java mod

Instructions on how to get the mod running on your machine can be found in the official [GDPC Interface](https://github.com/nilsgawlik/gdmc_http_interface/wiki/Installation) github repository. Once you have succesfully followed the given instrtuction you can go to the final step below!

### Launch the simulation

Once the environment is ready, simply starta single-player minecraft game and launch the `main.py` script and you're good to go !

```bash
python main.py
```
