# fantasyXC
Scripts to organise a Fantasy XC competition

Please note that, at the time of writing, I was trying to practice functional programming. 
This is reflected in a truly horrendous avoidance of class states.
 
## Getting started
Install Python (for example, via miniforge https://github.com/conda-forge/miniforge)

Install requirements via the command: `conda env create -f environment.yml` (see https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html for details)

Ensure input data is in correct format (see below)

Adjust match name in `matchScoring.py`

Run the script `matchScoring.py`

## Input data format
`teams/teams_2024.xlsx` (or whichever year you are in - edit in script) must contain the following columns:
* name
* team_name
* womens_player_1
* womens_player_2
* ...
* womens_player_8
* mens_player_1
* mens_player_2
* ...
* mens_player_8  

`raw_results/cuppers_2022_men.xlsx` (or whichever match it is) must contain the following columns:
* name
* score

`teams/aliases.xlsx` must contain the following columns:
* alt_name
* name