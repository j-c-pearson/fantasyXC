# matchScoring.py
import pandas as pd
import numpy as np

from scipy.optimize import milp
from scipy.optimize import LinearConstraint
from scipy.optimize import Bounds

def bonusPoints(results: pd.DataFrame, team: pd.DataFrame, match: str, team_type: str) -> int:
    # Add bonus points for players in their own team
    bonus_points = 0
    if match == 'cuppers_2024':
        for i in range(8):
            if team['name'].values[0] == team[f'{team_type}_player_{i+1}'].values[0]: # Only gives point if they spelled their own name consistently
                print(f'{team['name'].values[0]} is in their own team and so earns a bonus point')
                bonus_points = 1
    return bonus_points

def playerScoring(results: pd.DataFrame, player_name: str, aliases: pd.DataFrame) -> int:
    # Clean the player_name by stripping spaces and converting to lowercase
    player_name_cleaned = player_name.strip().lower()

    if player_name_cleaned in aliases['alt_name_cleaned'].values:
        player_name_cleaned = aliases[aliases['alt_name_cleaned'] == player_name_cleaned]['name_cleaned'].values[0]
    
    if player_name_cleaned not in results['name_cleaned'].values:
        print(f'{player_name} is not in the results and so scored 0')
        return 0
    else:
        player_score = results[results['name_cleaned'] == player_name_cleaned]['score'].values[0]
        return player_score

def teamScoring(results: pd.DataFrame, teams: pd.DataFrame, team_type: str, aliases: pd.DataFrame, captains: pd.DataFrame, match: str) -> pd.Series:
    # Clean the 'name' column in the results DataFrame
    results['name_cleaned'] = results['name'].str.strip().str.lower()
    # iterate through teams, adding up the scores for each player
    team_scores = []
    for team in teams['name']:
        team_score = 0
        # Score each player
        for i in range (8):
            player = teams[teams['name'] == team][f'{team_type}_player_{i+1}'].values[0]
            team_score += playerScoring(results, player, aliases)
        # Captains score double points
        if team in captains['name'].values:
            captain = captains[captains['name'] == team][f'{team_type}_captain'].values[0] # ERROR HERE
        else:
            captain = teams[teams['name'] == team][f'{team_type}_player_1'].values[0]
        team_score += playerScoring(results, captain, aliases)
        # Bonus points (e.g. for being in own team at beginning of season)
        team_score += bonusPoints(results, teams[teams['name'] == team], match, team_type)
        team_scores.append(team_score)
    return team_scores

def matchScoring(results_women: pd.DataFrame, results_men: pd.DataFrame, teams: pd.DataFrame, match: str, aliases: pd.DataFrame, captains: pd.DataFrame) -> pd.DataFrame:
    # iterate through teams, adding up the scores for each player
    teams[f'womens_{match}'] = teamScoring(results_women, teams, "womens", aliases, captains, match)
    teams[f'mens_{match}'] = teamScoring(results_men, teams, "mens", aliases, captains, match)
    teams[f'total_{match}'] = teams[f'womens_{match}'] + teams[f'mens_{match}']

    # Find the highest and lowest scores for combined teams
    max_score = teams[f'total_{match}'].max()
    max_score_i = teams[f'total_{match}'].idxmax()
    print(f"\nThe highest scoring team of this match was {teams['name'].iloc[max_score_i]} with {max_score}\n")

    min_score = teams[f'total_{match}'].min()
    min_score_i = teams[f'total_{match}'].idxmin()
    print(f"\nThe lowest scoring team of this match was {teams['name'].iloc[min_score_i]} with {min_score}\n")

    # Find the highest and lowest scores for women's teams
    max_womens_score = teams[f'womens_{match}'].max()
    max_womens_score_i = teams[f'womens_{match}'].idxmax()
    print(f"\nThe highest scoring women's team of this match was {teams['name'].iloc[max_womens_score_i]} with {max_womens_score}\n")

    min_womens_score = teams[f'womens_{match}'].min()
    min_womens_score_i = teams[f'womens_{match}'].idxmin()
    print(f"\nThe lowest scoring women's team of this match was {teams['name'].iloc[min_womens_score_i]} with {min_womens_score}\n")

    # Find the highest and lowest scores for men's teams
    max_mens_score = teams[f'mens_{match}'].max()
    max_mens_score_i = teams[f'mens_{match}'].idxmax()
    print(f"\nThe highest scoring men's team of this match was {teams['name'].iloc[max_mens_score_i]} with {max_mens_score}\n")

    min_mens_score = teams[f'mens_{match}'].min()
    min_mens_score_i = teams[f'mens_{match}'].idxmin()
    print(f"\nThe lowest scoring men's team of this match was {teams['name'].iloc[min_mens_score_i]} with {min_mens_score}\n")

    # Return the data
    return teams

def playerCosting(costs: pd.DataFrame, player_name: str, aliases: pd.DataFrame) -> int:
    # Clean the player_name by stripping spaces and converting to lowercase
    player_name_cleaned = player_name.strip().lower()

    # if the player is in the costs DataFrame, return the cost
    if player_name_cleaned in costs['name_cleaned'].values:
        player_cost = costs[costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
    # if the player is in the aliases DataFrame, but not the costs DataFrame, try the alt_name
    elif player_name_cleaned in aliases['name_cleaned'].values:
        player_name_cleaned = aliases[aliases['name_cleaned'] == player_name_cleaned]['alt_name_cleaned'].values[0]
        if player_name_cleaned in costs['name_cleaned'].values:
            player_cost = costs[costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
        else:
            print(f'{player_name} is not in a band and so costs 1')
            player_cost = 1
    # if the player is not in the costs or aliases DataFrame, return 1
    else:
            print(f'{player_name} is not in a band and so costs 1')
            player_cost = 1       
    return player_cost

def makeCostMatrix(results: pd.DataFrame, costs: pd.DataFrame, aliases: pd.DataFrame) -> tuple:
    costs['name_cleaned'] = costs['name'].str.strip().str.lower()
    # Create a list of names
    names = results['name'].values
    # Create a vector of scores
    score_vector = results['score'].values

    # Create a matrix of costs
    cost_matrix = np.ones(len(names))
    for i in range(len(names)):
        cost_matrix[i] = playerCosting(costs, names[i], aliases)
    
    return score_vector, cost_matrix, names

def optimalTeam(results: pd.DataFrame, costs: pd.DataFrame, aliases: pd.DataFrame) -> None:
    score_vector, cost_matrix, names = makeCostMatrix(results, costs, aliases)
    constraint_matrix = np.vstack([cost_matrix, np.ones(len(score_vector))])
    lower_bounds = [0, 8]
    upper_bounds = [24, 8]
    constraints = LinearConstraint(constraint_matrix, lower_bounds, upper_bounds)
    bounds = Bounds(0, 1)
    # Solve the MILP
    res = milp(c=-1*score_vector, integrality=[1]*len(score_vector), bounds=bounds, constraints=constraints)

    print(f'Solver has completed with status: {res.message}')
    print(f'The optimal team is {names[res.x == 1]}')
    print(f'The optimal team has a score (pre-captain) of {-1*res.fun}')

if __name__ == '__main__':
    # Competition to evaluate
    # CHANGE THIS TO THE EVENT YOU WANT TO EVALUATE
    match = 'bbo_2024' # input match to evaluate


    # Read in the data
    matchWomen = pd.read_excel(f'raw_results/{match}_women.xlsx')
    matchMen = pd.read_excel(f'raw_results/{match}_men.xlsx')
    teams = pd.read_excel('teams/teams_2024.xlsx')
    aliases = pd.read_excel('teams/aliases.xlsx')
    aliases['alt_name_cleaned'] = aliases['alt_name'].str.strip().str.lower()
    aliases['name_cleaned'] = aliases['name'].str.strip().str.lower()
    captains = pd.read_excel('teams/captains_2024.xlsx')
    costs = pd.read_excel('teams/costs.xlsx')
    costs['name_cleaned'] = costs['name'].str.strip().str.lower()

    # Create columns of sum of men's and women's scores
    teams = matchScoring(matchWomen, matchMen, teams, match, aliases, captains)

    # Print the data
    match_scores = teams[['name', 'team_name', f'womens_{match}', f'mens_{match}', f'total_{match}']]
    match_scores = match_scores.sort_values(by=f'total_{match}', ascending=False)
    
    print(f'\n\nScores for {match}')
    print(match_scores)
    print(f'\n\nWomen\'s scores for {match}')
    print(match_scores.sort_values(by=f'womens_{match}', ascending=False))
    print(f'\n\nMen\'s scores for {match}')
    print(match_scores.sort_values(by=f'mens_{match}', ascending=False))

    # save data
    match_scores.to_excel(f'scores/scores_{match}.xlsx', index=False)

    # Compute the optimal teams
    optimalTeam(matchWomen, costs, aliases)
    optimalTeam(matchMen, costs, aliases)