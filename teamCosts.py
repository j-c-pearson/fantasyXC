# matchScoring.py
import pandas as pd
import os
        
class Teams:
    def __init__(self):
        # Read in the data
        self.teams = pd.read_excel('teams/teams_2024.xlsx')
        self.aliases = pd.read_excel('teams/aliases.xlsx')
        self.aliases['alt_name_cleaned'] = self.aliases['alt_name'].str.strip().str.lower()
        self.aliases['name_cleaned'] = self.aliases['name'].str.strip().str.lower()
        self.captains = pd.read_excel('teams/captains_2024.xlsx')
        self.costs = pd.read_excel('teams/costs.xlsx')
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()

    def playerCosting(self, player_name: str) -> int:
        """
        Function to return the cost of a player
        Used to create constraints for MILP solver
        """
        # Clean the player_name by stripping spaces and converting to lowercase
        player_name_cleaned = player_name.strip().lower()

        # if the player is in the costs DataFrame, return the cost
        if player_name_cleaned in self.costs['name_cleaned'].values:
            player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
        # if the player is in the aliases DataFrame, but not the costs DataFrame, try the alt_name
        elif player_name_cleaned in self.aliases['alt_name_cleaned'].values:
            player_name_cleaned = self.aliases[self.aliases['alt_name_cleaned'] == player_name_cleaned]['name_cleaned'].values[0]
            if player_name_cleaned in self.costs['name_cleaned'].values:
                player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
            else:
                print(f'{player_name} is not in a band and so costs 1')
                player_cost = 1
        elif player_name_cleaned in self.aliases['name_cleaned'].values:
            player_name_cleaned = self.aliases[self.aliases['name_cleaned'] == player_name_cleaned]['alt_name_cleaned'].values[0]
            if player_name_cleaned in self.costs['name_cleaned'].values:
                player_cost = self.costs[self.costs['name_cleaned'] == player_name_cleaned]['cost'].values[0]
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
                player_name = self.teams[self.teams['name'] == team][f'{team_type}_player_{i+1}'].values[0]
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
        over_budget_teams = team_costs[(team_costs['womens_cost'] > 24) | (team_costs['mens_cost'] > 24)]
        print('~~~~~~~~~~~~~~~~~~~~~~~~~Teams Over Budget~~~~~~~~~~~~~~~~~~~~~~~~~')
        over_budget_teams_temp = over_budget_teams[['name', 'team_name', 'womens_cost', 'mens_cost']]
        over_budget_teams_temp.to_excel('teams/overbudget.xlsx', index=False)
        print(over_budget_teams_temp)

    def check_new_costs(self):
        # read new costs file
        self.costs_old = self.costs
        self.costs = pd.read_excel('teams/costs_new.xlsx')
        self.costs['name_cleaned'] = self.costs['name'].str.strip().str.lower()
        team_costs = self.find_team_costs()
        print('~~~~~~~~~~~~~~~~~~~~~~~~~New Team Costs~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(team_costs)
        additional_budget_teams = team_costs[(team_costs['womens_cost'] > 24) | (team_costs['mens_cost'] > 24)]
        print('~~~~~~~~~~~~~~~~~~~~~~~~~Teams with additional Budget~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(additional_budget_teams)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~New Team Budgets~~~~~~~~~~~~~~~~~~~~~~~~~')
        team_costs['womens_budget_new'] = team_costs['womens_cost'].apply(lambda x: max(24, x))
        team_costs['mens_budget_new'] = team_costs['mens_cost'].apply(lambda x: max(24, x))
        team_costs_temp = team_costs[['name', 'team_name', 'womens_budget_new', 'mens_budget_new']]
        print(team_costs_temp)
        team_costs_temp.to_excel('teams/team_budgets_new.xlsx', index=False)

        # revert to old costs
        self.costs_new = self.costs
        self.costs = self.costs_old


if __name__ == '__main__':

    teams = Teams()
    teams.check_team_costs()
    
    if os.path.exists('teams/costs_new.xlsx'):
        teams.check_new_costs()