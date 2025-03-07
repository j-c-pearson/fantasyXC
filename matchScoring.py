# matchScoring.py
import os
import pandas as pd
import numpy as np

from scipy.optimize import milp
from scipy.optimize import LinearConstraint
from scipy.optimize import Bounds

class Match:
    """scores a single match"""
    def __init__(self, match_name: str):
        # Read in the data
        self.match_name = match_name
        self.matchWomen = pd.read_excel(f'raw_results/{self.match_name}_women.xlsx')
        self.matchMen = pd.read_excel(f'raw_results/{self.match_name}_men.xlsx')
        self.teams = pd.read_excel('teams/teams_2024.xlsx')
        self.aliases = pd.read_excel('teams/aliases.xlsx')
        self.aliases['alt_name_cleaned'] = self.aliases['alt_name'].str.strip().str.lower()
        self.aliases['name_cleaned'] = self.aliases['name'].str.strip().str.lower()
        self.captains = pd.read_excel('teams/captains_2024.xlsx')
        self.costs = pd.read_excel('teams/costs.xlsx')
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()

    def bonusPoints(self, results: pd.DataFrame, team: pd.DataFrame, team_type: str) -> int:
        # Add bonus points for players in their own team
        bonus_points = 0
        if self.match_name == 'cuppers_2024':
            for i in range(8):
                if team['name'].values[0] == team[f'{team_type}_player_{i+1}'].values[0]:
                    # Only gives point if they spelled their own name consistently
                    print((f'{team['name'].values[0]} is in their own team '
                           'and so earns a bonus point'))
                    bonus_points = 1
        return bonus_points

    def playerScoring(self, results: pd.DataFrame, player_name: str) -> int:
        # Clean the player_name by stripping spaces and converting to lowercase
        player_name_cleaned = player_name.strip().lower()

        # if the player is in the results DataFrame, return the score
        if player_name_cleaned in results['name_cleaned'].values:
            player_score = results[results['name_cleaned'] == \
                                   player_name_cleaned]['score'].values[0]
            return player_score
        else:
            # if the player is in the aliases DataFrame, but not the results DataFrame,
            # try the alt_name
            if player_name_cleaned in self.aliases['alt_name_cleaned'].values:
                player_name_cleaned = self.aliases[self.aliases['alt_name_cleaned'] == \
                                                   player_name_cleaned]['name_cleaned'].values[0]
            elif player_name_cleaned in self.aliases['name_cleaned'].values:
                player_name_cleaned = self.aliases[self.aliases['name_cleaned']\
                                            == player_name_cleaned]['alt_name_cleaned'].values[0]

            if player_name_cleaned in results['name_cleaned'].values:
                player_score = results[results['name_cleaned'] == \
                                       player_name_cleaned]['score'].values[0]
                return player_score
            else:
                print(f'{player_name} is not in the results and so scored 0')
                return 0

    def teamScoring(self, results: pd.DataFrame, team_type: str) -> pd.Series:
        """iterates through teams, adding scores for each player"""
        # Clean the 'name' column in the results DataFrame
        results['name_cleaned'] = results['name'].str.strip().str.lower()
        # iterate through teams, adding up the scores for each player
        team_scores = []
        for team in self.teams['name']:
            team_score = 0
            # Score each player
            for i in range (8):
                player = self.teams[self.teams['name'] == team]\
                    [f'{team_type}_player_{i+1}'].values[0]
                team_score += self.playerScoring(results, player)
            # Captains score double points
            if team in self.captains['name'].values:
                captain = self.captains[self.captains['name'] == team]\
                    [f'{team_type}_captain'].values[0] # ERROR HERE
            else:
                captain = self.teams[self.teams['name'] == team][f'{team_type}_player_1'].values[0]
            team_score += self.playerScoring(results, captain)
            # Bonus points (e.g. for being in own team at beginning of season)
            team_score += self.bonusPoints(results, 
                                           self.teams[self.teams['name'] == team], 
                                           team_type
                                           )
            team_scores.append(team_score)
        return team_scores

    def matchScoring(self, verbose=False) -> pd.DataFrame:
        """scores a single match"""
        # iterate through teams, adding up the scores for each player
        self.teams[f'womens_{self.match_name}'] = self.teamScoring(self.matchWomen, "womens")
        self.teams[f'mens_{self.match_name}'] = self.teamScoring(self.matchMen, "mens")
        self.teams[f'total_{self.match_name}'] = self.teams[f'womens_{self.match_name}'] + \
            self.teams[f'mens_{self.match_name}']

        if verbose == True:
            # Find the highest and lowest scores for combined teams
            max_score = self.teams[f'total_{self.match_name}'].max()
            max_score_i = self.teams[f'total_{self.match_name}'].idxmax()
            print(("\nThe highest scoring team of this match was "
                   f"{self.teams['name'].iloc[max_score_i]} with {max_score}\n"))

            min_score = self.teams[f'total_{self.match_name}'].min()
            min_score_i = self.teams[f'total_{self.match_name}'].idxmin()
            print(("\nThe lowest scoring team of this match was "
                   f"{self.teams['name'].iloc[min_score_i]} with {min_score}\n"))

            # Find the highest and lowest scores for women's teams
            max_womens_score = self.teams[f'womens_{self.match_name}'].max()
            max_womens_score_i = self.teams[f'womens_{self.match_name}'].idxmax()
            print(("\nThe highest scoring women's team of this match was "
                   f"{self.teams['name'].iloc[max_womens_score_i]} with {max_womens_score}\n"))

            min_womens_score = self.teams[f'womens_{self.match_name}'].min()
            min_womens_score_i = self.teams[f'womens_{self.match_name}'].idxmin()
            print(("\nThe lowest scoring women's team of this match was "
                   f"{self.teams['name'].iloc[min_womens_score_i]} with {min_womens_score}\n"))

            # Find the highest and lowest scores for men's teams
            max_mens_score = self.teams[f'mens_{self.match_name}'].max()
            max_mens_score_i = self.teams[f'mens_{self.match_name}'].idxmax()
            print(("\nThe highest scoring men's team of this match was "
                   f"{self.teams['name'].iloc[max_mens_score_i]} with {max_mens_score}\n"))

            min_mens_score = self.teams[f'mens_{self.match_name}'].min()
            min_mens_score_i = self.teams[f'mens_{self.match_name}'].idxmin()
            print(("\nThe lowest scoring men's team of this match was "
                   f"{self.teams['name'].iloc[min_mens_score_i]} with {min_mens_score}\n"))

        # Print the data
        match_scores = self.teams[['name', 'team_name', f'womens_{self.match_name}',\
                                   f'mens_{self.match_name}', f'total_{self.match_name}']]
        match_scores = match_scores.sort_values(by=f'total_{self.match_name}', ascending=False)

        if verbose == True:
            print(f'\n\nScores for {self.match_name}')
            print(match_scores)
            print(f'\n\nWomen\'s scores for {self.match_name}')
            print(match_scores.sort_values(by=f'womens_{self.match_name}', ascending=False))
            print(f'\n\nMen\'s scores for {self.match_name}')
            print(match_scores.sort_values(by=f'mens_{self.match_name}', ascending=False))

        # save data
        match_scores.to_excel(f'scores/scores_{self.match_name}.xlsx', index=False)

        # Return the data
        return self.teams

    def playerCosting(self, player_name: str) -> int:
        """
        Function to return the cost of a player
        Used to create constraints for MILP solver
        """
        # Clean the player_name by stripping spaces and converting to lowercase
        player_name_cleaned = player_name.strip().lower()

        # if the player is in the costs DataFrame, return the cost
        if player_name_cleaned in self.costs['name_cleaned'].values:
            player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]\
                ['cost'].values[0]
        # if the player is in the aliases DataFrame, but not the costs DataFrame, try the alt_name
        elif player_name_cleaned in self.aliases['alt_name_cleaned'].values:
            player_name_cleaned = self.aliases[self.aliases['alt_name_cleaned'] == \
                                               player_name_cleaned]['name_cleaned'].values[0]
            if player_name_cleaned in self.costs['name_cleaned'].values:
                player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]\
                    ['cost'].values[0]
            else:
                print(f'{player_name} is not in a band and so costs 1')
                player_cost = 1
        elif player_name_cleaned in self.aliases['name_cleaned'].values:
            player_name_cleaned = self.aliases[self.aliases['name_cleaned'] == player_name_cleaned]\
                ['alt_name_cleaned'].values[0]
            if player_name_cleaned in self.costs['name_cleaned'].values:
                player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]\
                    ['cost'].values[0]
            else:
                print(f'{player_name} is not in a band and so costs 1')
                player_cost = 1
        # if the player is not in the costs or aliases DataFrame, return 1
        else:
            print(f'{player_name} is not in a band and so costs 1')
            player_cost = 1
        return player_cost

    def makeCostMatrix(self, results: pd.DataFrame) -> tuple:
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()
        # Create a list of names
        names = results['name'].values
        # Create a vector of scores
        score_vector = results['score'].values

        # Create a matrix of costs
        cost_matrix = np.ones(len(names))
        for i, name in enumerate(names):
            cost_matrix[i] = self.playerCosting(name)

        return score_vector, cost_matrix, names

    def optimalTeam(self, results: pd.DataFrame) -> None:
        score_vector, cost_matrix, names = self.makeCostMatrix(results)
        constraint_matrix = np.vstack([cost_matrix, np.ones(len(score_vector))])
        lower_bounds = [0, 8]
        upper_bounds = [24, 8]
        constraints = LinearConstraint(constraint_matrix, lower_bounds, upper_bounds)
        bounds = Bounds(0, 1)
        # Solve the MILP
        res = milp(c=-1*score_vector,
                   integrality=[1]*len(score_vector),
                   bounds=bounds,
                   constraints=constraints
                   )

        print(f'Solver has completed with status: {res.message}')
        print(f'The optimal team is {names[res.x == 1]}')
        print(f'The optimal team has a score (pre-captain) of {-1*res.fun}')

    def optimalTeams(self) -> None:
        self.optimalTeam(self.matchWomen)
        self.optimalTeam(self.matchMen)
        
class Teams:
    """handles teams and their cost"""
    def __init__(self):
        # Read in the data
        self.teams = pd.read_excel('teams/teams_2024.xlsx')
        self.aliases = pd.read_excel('teams/aliases.xlsx')
        self.aliases['alt_name_cleaned'] = self.aliases['alt_name'].str.strip().str.lower()
        self.aliases['name_cleaned'] = self.aliases['name'].str.strip().str.lower()
        self.captains = pd.read_excel('teams/captains_2024.xlsx')
        self.costs = pd.read_excel('teams/costs.xlsx')
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()
        if os.path.exists('teams/costs_new.xlsx'):
            self.costs_new = pd.read_excel('teams/costs_new.xlsx')
            self.costs_new['name_cleaned'] = self.costs['name'].str.strip().str.lower()
        else:
            self.costs_new = None

    def playerCosting(self, player_name: str) -> int:
        """
        Function to return the cost of a player
        Used to create constraints for MILP solver
        """
        # Clean the player_name by stripping spaces and converting to lowercase
        player_name_cleaned = player_name.strip().lower()

        # if the player is in the costs DataFrame, return the cost
        if player_name_cleaned in self.costs['name_cleaned'].values:
            player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]\
                ['cost'].values[0]
        # if the player is in the aliases DataFrame, but not the costs DataFrame, try the alt_name
        elif player_name_cleaned in self.aliases['alt_name_cleaned'].values:
            player_name_cleaned = self.aliases[self.aliases['alt_name_cleaned'] == \
                                               player_name_cleaned]['name_cleaned'].values[0]
            if player_name_cleaned in self.costs['name_cleaned'].values:
                player_cost = self.costs[self.costs['name_cleaned'] == \
                                         player_name_cleaned]['cost'].values[0]
            else:
                print(f'{player_name} is not in a band and so costs 1')
                player_cost = 1
        elif player_name_cleaned in self.aliases['name_cleaned'].values:
            player_name_cleaned = self.aliases[self.aliases['name_cleaned'] == player_name_cleaned]\
                ['alt_name_cleaned'].values[0]
            if player_name_cleaned in self.costs['name_cleaned'].values:
                player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]\
                    ['cost'].values[0]
            else:
                print(f'{player_name} is not in a band and so costs 1')
                player_cost = 1
        # if the player is not in the costs or aliases DataFrame, return 1
        else:
            print(f'{player_name} is not in a band and so costs 1')
            player_cost = 1
        return player_cost

    def teamCosting(self, team_type: str) -> pd.Series:
        # iterate through teams, adding up the scores for each player
        team_costs = []
        for team in self.teams['name']:
            team_cost = 0
            # Cost each player
            for i in range (8):
                player_name = self.teams[self.teams['name'] == team]\
                    [f'{team_type}_player_{i+1}'].values[0]
                team_cost += self.playerCosting(player_name)
            team_costs.append(team_cost)
        return team_costs

    def find_team_costs(self) -> pd.DataFrame:
        self.teams['womens_cost'] = self.teamCosting("womens")
        self.teams['mens_cost'] = self.teamCosting("mens")
        return self.teams

    def check_team_costs(self):
        team_costs = self.find_team_costs()
        print('\n\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~Team Costs~~~~~~~~~~~~~~~~~~~~~~~~~\n\n\n\n')
        print(team_costs)
        over_budget_teams = \
            team_costs[(team_costs['womens_cost'] > 24) | (team_costs['mens_cost'] > 24)]
        print('\n\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~Teams Over Budget~~~~~~~~~~~~~~~~~~~~~~~~~\n\n\n\n')
        print(over_budget_teams)

    def check_new_costs(self):
        # read new costs file
        costs_old = self.costs
        self.costs = pd.read_excel('teams/costs_new.xlsx')
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()
        team_costs = self.find_team_costs()
        print('\n\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~New Team Costs~~~~~~~~~~~~~~~~~~~~~~~~~\n\n\n\n')
        print(team_costs)
        additional_budget_teams = \
            team_costs[(team_costs['womens_cost'] > 24) | (team_costs['mens_cost'] > 24)]
        print('\n\n\n\n~~~~~~~~~~~~~~~~~~~Teams with additional Budget~~~~~~~~~~~~~~~~~\n\n\n\n')
        print(additional_budget_teams)
        # revert to old costs
        self.costs_new = self.costs
        self.costs = costs_old


if __name__ == '__main__':
    # Competition to evaluate
    # CHANGE THIS TO THE EVENT YOU WANT TO EVALUATE
    match_name = 'bucs_2025' # input match to evaluate

    print('Running matchScoring.py')
    print('\n\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~fantXC~~~~~~~~~~~~~~~~~~~~~~~~~\n\n\n\n')

    match_to_score = Match(match_name)

    # Create columns of sum of men's and women's scores
    teams = match_to_score.matchScoring(verbose=True)

    # Compute the optimal teams
    match_to_score.optimalTeams()

    teams = Teams()
    teams.check_team_costs()
