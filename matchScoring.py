# matchScoring.py
import pandas as pd
import numpy as np

from scipy.optimize import milp
from scipy.optimize import LinearConstraint
from scipy.optimize import Bounds

class Match:
    def __init__(self, match_name: str):
        # Read in the data
        self.match_name = match_name
        self.matchWomen = pd.read_excel(f'raw_results/{match_name}_women.xlsx')
        self.matchMen = pd.read_excel(f'raw_results/{match_name}_men.xlsx')
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
                if team['name'].values[0] == team[f'{team_type}_player_{i+1}'].values[0]: # Only gives point if they spelled their own name consistently
                    print(f'{team['name'].values[0]} is in their own team and so earns a bonus point')
                    bonus_points = 1
        return bonus_points

    def playerScoring(self, results: pd.DataFrame, player_name: str) -> int:
        # Clean the player_name by stripping spaces and converting to lowercase
        player_name_cleaned = player_name.strip().lower()

        # if the player is in the results DataFrame, return the score
        if player_name_cleaned in results['name_cleaned'].values:
            player_score = results[results['name_cleaned'] == player_name_cleaned]['score'].values[0]
            return player_score
        else: 
            # if the player is in the aliases DataFrame, but not the results DataFrame, try the alt_name
            if player_name_cleaned in self.aliases['alt_name_cleaned'].values:
                player_name_cleaned = self.aliases[self.aliases['alt_name_cleaned'] == player_name_cleaned]['name_cleaned'].values[0]
            elif player_name_cleaned in self.aliases['name_cleaned'].values:
                player_name_cleaned = self.aliases[self.aliases['name_cleaned'] == player_name_cleaned]['alt_name_cleaned'].values[0]

            if player_name_cleaned in results['name_cleaned'].values:
                player_score = results[results['name_cleaned'] == player_name_cleaned]['score'].values[0]
                return player_score
            else:
                print(f'{player_name} is not in the results and so scored 0')
                return 0

    def teamScoring(self, results: pd.DataFrame, team_type: str) -> pd.Series:
        # Clean the 'name' column in the results DataFrame
        results['name_cleaned'] = results['name'].str.strip().str.lower()
        # iterate through teams, adding up the scores for each player
        team_scores = []
        for team in self.teams['name']:
            team_score = 0
            # Score each player
            for i in range (8):
                player = self.teams[self.teams['name'] == team][f'{team_type}_player_{i+1}'].values[0]
                team_score += self.playerScoring(results, player)
            # Captains score double points
            if team in self.captains['name'].values:
                captain = self.captains[self.captains['name'] == team][f'{team_type}_captain'].values[0] # ERROR HERE
            else:
                captain = self.teams[self.teams['name'] == team][f'{team_type}_player_1'].values[0]
            team_score += self.playerScoring(results, captain)
            # Bonus points (e.g. for being in own team at beginning of season)
            team_score += self.bonusPoints(results, self.teams[self.teams['name'] == team], team_type)
            team_scores.append(team_score)
        return team_scores

    def matchScoring(self) -> pd.DataFrame:
        # iterate through teams, adding up the scores for each player
        self.teams[f'womens_{self.match_name}'] = self.teamScoring(self.matchWomen, "womens")
        self.teams[f'mens_{self.match_name}'] = self.teamScoring(self.matchMen, "mens")
        self.teams[f'total_{self.match_name}'] = self.teams[f'womens_{self.match_name}'] + self.teams[f'mens_{self.match_name}']

        # Find the highest and lowest scores for combined teams
        max_score = self.teams[f'total_{self.match_name}'].max()
        max_score_i = self.teams[f'total_{self.match_name}'].idxmax()
        print(f"\nThe highest scoring team of this match was {self.teams['name'].iloc[max_score_i]} with {max_score}\n")

        min_score = self.teams[f'total_{self.match_name}'].min()
        min_score_i = self.teams[f'total_{self.match_name}'].idxmin()
        print(f"\nThe lowest scoring team of this match was {self.teams['name'].iloc[min_score_i]} with {min_score}\n")

        # Find the highest and lowest scores for women's teams
        max_womens_score = self.teams[f'womens_{self.match_name}'].max()
        max_womens_score_i = self.teams[f'womens_{self.match_name}'].idxmax()
        print(f"\nThe highest scoring women's team of this match was {self.teams['name'].iloc[max_womens_score_i]} with {max_womens_score}\n")

        min_womens_score = self.teams[f'womens_{self.match_name}'].min()
        min_womens_score_i = self.teams[f'womens_{self.match_name}'].idxmin()
        print(f"\nThe lowest scoring women's team of this match was {self.teams['name'].iloc[min_womens_score_i]} with {min_womens_score}\n")

        # Find the highest and lowest scores for men's teams
        max_mens_score = self.teams[f'mens_{self.match_name}'].max()
        max_mens_score_i = self.teams[f'mens_{self.match_name}'].idxmax()
        print(f"\nThe highest scoring men's team of this match was {self.teams['name'].iloc[max_mens_score_i]} with {max_mens_score}\n")

        min_mens_score = self.teams[f'mens_{self.match_name}'].min()
        min_mens_score_i = self.teams[f'mens_{self.match_name}'].idxmin()
        print(f"\nThe lowest scoring men's team of this match was {self.teams['name'].iloc[min_mens_score_i]} with {min_mens_score}\n")

        # Return the data
        return self.teams

    def playerCosting(self, costs: pd.DataFrame, player_name: str, aliases: pd.DataFrame) -> int:
        """
        Function to return the cost of a player
        Used to create constraints for MILP solver
        """
        # Clean the player_name by stripping spaces and converting to lowercase
        player_name_cleaned = player_name.strip().lower()

        # if the player is in the costs DataFrame, return the cost
        if player_name_cleaned in costs['name_cleaned'].values:
            player_cost = costs[costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
        # if the player is in the aliases DataFrame, but not the costs DataFrame, try the alt_name
        elif player_name_cleaned in aliases['alt_name_cleaned'].values:
            player_name_cleaned = aliases[aliases['alt_name_cleaned'] == player_name_cleaned]['name_cleaned'].values[0]
            if player_name_cleaned in costs['name_cleaned'].values:
                player_cost = costs[costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
            else:
                print(f'{player_name} is not in a band and so costs 1')
                player_cost = 1
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

    def makeCostMatrix(self, results: pd.DataFrame) -> tuple:
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()
        # Create a list of names
        names = results['name'].values
        # Create a vector of scores
        score_vector = results['score'].values

        # Create a matrix of costs
        cost_matrix = np.ones(len(names))
        for i in range(len(names)):
            cost_matrix[i] = self.playerCosting(self.costs, names[i], self.aliases)
        
        return score_vector, cost_matrix, names

    def optimalTeam(self, results: pd.DataFrame) -> None:
        score_vector, cost_matrix, names = self.makeCostMatrix(results)
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

    def optimalTeams(self) -> None:
        match_to_score.optimalTeam(self.matchWomen)
        match_to_score.optimalTeam(self.matchMen)
        

if __name__ == '__main__':
    # Competition to evaluate
    # CHANGE THIS TO THE EVENT YOU WANT TO EVALUATE
    match_name = 'varsity_2024' # input match to evaluate

    print('Running matchScoring.py')
    print('\n\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~fantXC~~~~~~~~~~~~~~~~~~~~~~~~~\n\n\n\n')

    match_to_score = Match(match_name)

    # Create columns of sum of men's and women's scores
    teams = match_to_score.matchScoring()

    # Print the data
    match_scores = teams[['name', 'team_name', f'womens_{match_name}', f'mens_{match_name}', f'total_{match_name}']]
    match_scores = match_scores.sort_values(by=f'total_{match_name}', ascending=False)
    
    print(f'\n\nScores for {match_name}')
    print(match_scores)
    print(f'\n\nWomen\'s scores for {match_name}')
    print(match_scores.sort_values(by=f'womens_{match_name}', ascending=False))
    print(f'\n\nMen\'s scores for {match_name}')
    print(match_scores.sort_values(by=f'mens_{match_name}', ascending=False))

    # save data
    match_scores.to_excel(f'scores/scores_{match_name}.xlsx', index=False)

    # Compute the optimal teams
    match_to_score.optimalTeams()
    