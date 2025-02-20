# seriesScoring.py
"""Scores all matches in series using config file and saves to excel file"""
from datetime import datetime
import pandas as pd
import yaml
from matchScoring import Match

if __name__ == '__main__':
    print('\n\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~fantXC~~~~~~~~~~~~~~~~~~~~~~~~~\n\n\n\n')

    # load config file
    with open("config.yml", encoding='utf-8') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    # create scores dataFrame
    matches_list = cfg['matches']
    num_matches = len(matches_list)
    for i in range(num_matches):
        match = matches_list[i]
        match_name = match['name']
        match_weight = match['weight']
        match_date = match['date']

        current_date = datetime.now().date()
        if match_date > current_date:
            print('Not evaluating future match: ', match_name)
            continue

        try :
            match_data = pd.read_excel('scores/scores_' + match_name + '.xlsx')
        except FileNotFoundError:
            print('Scoring match: ', match_name)
            match_to_score = Match(match_name)
            _ = match_to_score.matchScoring(verbose=False)
            match_data = pd.read_excel('scores/scores_' + match_name + '.xlsx')

        if i == 0:
            match_data = match_data.drop(columns=[f'total_{match_name}'])
            series_scores_df = match_data
        else:
            match_data = match_data.drop(columns=['team_name', f'total_{match_name}'])
            series_scores_df = pd.merge(series_scores_df, match_data, on='name', how='outer')

    # Create gender totals
    for i in range(num_matches):
        current_date = datetime.now().date()
        if matches_list[i]["date"] > current_date:
            # print('Not evaluating future match: ', match_name)
            continue

        if i == 0:
            series_scores_df['total_men'] = matches_list[i]["weight"] * \
                series_scores_df[f'mens_{matches_list[i]["name"]}']
            series_scores_df['total_women'] = matches_list[i]["weight"] * \
                series_scores_df[f'womens_{matches_list[i]["name"]}']
            series_scores_df['total_all'] = series_scores_df['total_men'] + \
                series_scores_df['total_women']
        else:
            series_scores_df['total_men'] = matches_list[i]["weight"] * \
                series_scores_df['total_men'] + series_scores_df[f'mens_{matches_list[i]["name"]}']
            series_scores_df['total_women'] = matches_list[i]["weight"] * \
                series_scores_df['total_women'] + \
                series_scores_df[f'womens_{matches_list[i]["name"]}']
            series_scores_df['total_all'] = series_scores_df['total_all'] + \
                matches_list[i]["weight"] * series_scores_df[f'mens_{matches_list[i]["name"]}'] + \
                matches_list[i]["weight"] * series_scores_df[f'womens_{matches_list[i]["name"]}']

    series_scores_df = series_scores_df.sort_values(by='total_all', ascending=False)

    print(series_scores_df)

    series_scores_df.to_excel('scores/series_scores.xlsx', index=False)
    print('Saved series scores to excel file')
