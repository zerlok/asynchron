#!/bin/bash

# Waiting for https://github.com/python-poetry/poetry/issues/3413 to be resolved
# sed expression is built based on https://stackoverflow.com/questions/68203376/how-to-list-the-name-of-all-poetry-extras/68216833#68216833
poetry install $( sed --quiet '/\[tool\.poetry\.extras\]/,/^\[/{s/^\(.*\) = \[.*/-E \1/p}' pyproject.toml )
