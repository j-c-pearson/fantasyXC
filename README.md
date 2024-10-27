# fantasyXC
Scripts to organise a Fantasy XC competition
 
## Suggested use
Install Python via miniforge: https://github.com/conda-forge/miniforge

Install requirements via the command: `conda env create -f environment.yml` (see https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html for details)

Ensure input data is in correct format (see below)

Adjust match name in `matchScoring.py`

Run the script `matchScoring.py`

## input data format
`teams_2024.xlsx` (or whichever year you are in - edit in script) must contain the following columns:
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
`cuppers_2022_men.xlsx` (or whichever match it is) must contain the following columns:
* name
* score