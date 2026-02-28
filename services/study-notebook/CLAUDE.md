# Project Description

The goal of this project is to have a tool to study financial data
of public listed companies.

# Features

## Stock Analysis
- Source data is taken from api-explorer (../api-explorer). The api-explorer endpoint
is configured via a configuration variable.
- The method of interest to us is stock info.
- An analysis is an abstract entity.
- We create analysis through a wizard.
    1. Each analysis contains one or more scores.
    2. A math score is a mathematical expression composed of metrics from the data source.
    3. A normalized score is a list of metrics from data source where each value is normalized between -1 and 1 with respect all the realized values of the metric. A weight is then assigned to each normalized metric and a mathematical expression defines the score.
    4. Some metrics are negatively oriented: the lower the best; while others are positively oriented: the higher the best.
- We have a tool to help us writing scores. For example, to pick one of the availables metrics when we are writing an expression.
- After an analysis is created, it can be realized over one or more tickers.
- We have a ticker manager that help us to organize tickers within collections (a ticker can be part of one or more collections). We can add or remove a ticker from a collection.
    - You can use the lookup endpoint of api-explorer to help search tickers.
- The realization of an analysis will run the score for each ticker and then display the results in a table.



# Stack

- python
- tox
    - ruff
    - pyright
    - pytest
- uvicorn
- fastapi

# Structure

- src/
    - study_notebook/
        - core/
            - model.py
            - api.py
        - cli/
        - utils/
            - config.py
            - utils.py
        - server/
- test
- pyproject.toml
- .env
- .env.example

## Guidelines

- Configuration variables are specified on the .env file.
- Use a Configuration class with pydantic and dotenv to load configuration variables
- Modules in core are not allowed to import other project modules that are not in the core package.
- Modules in cli package are allowed to import from core package only.
- Modules in server are allowed to import from core and visualization packages.
- Always test using tox.

