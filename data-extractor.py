import datetime
import os
import json
from json import JSONDecodeError

import pandas as pd


AVAILABLE_BENCHMARK_VERSIONS: list[str] = ['v0.9', 'v1.0', 'v1.5', 'v1.5_quantized', 'v1.6', 'v1.6_quantized']
AVAILABLE_COLUMNS_TO_KEEP: list = ['game', 'model', 'experiment', 'episode', 'Aborted', 'Lose', 'Success']
AVAILABLE_GAMES: list = ['privateshared', 'referencegame', 'taboo', 'wordle', 'wordle_withclue', 'wordle_withcritic', 'imagegame']

"""
This class represents a data extractor that enables the extraction of the episodes of all games, experiments and episodes
for all models. The data is stored as JSON files such that each episode is saved as a list of interactions in the huggingface chat format.

The extractor works on the raw.csv files of each benchmark version. There, all model, game, experiment and episode
information is extracted to collect the conversation data.
"""
class DataExtractor:

    def __init__(self, benchmark_versions: list[str]=None, columns_to_keep: list[str]=None, games_to_extract: list[str]=None, output_dir: str = None):
        if benchmark_versions is None:
            benchmark_versions = AVAILABLE_BENCHMARK_VERSIONS
        if columns_to_keep is None:
            columns_to_keep = AVAILABLE_COLUMNS_TO_KEEP
        if games_to_extract is None:
            games_to_extract = AVAILABLE_GAMES
        if output_dir is None:
            output_dir = os.getcwd() + '/extracted-data-' + '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
            self.create_output_dir(path=output_dir)

        self.USER = "user"
        self.ASSISTANT = "assistant"
        self.benchmark_versions = benchmark_versions
        self.columns_to_keep = columns_to_keep
        self.games_to_extract = games_to_extract
        self.output_dir = output_dir

        # check consistency
        self.check_benchmark_version_consistency()
        self.check_games_consistency()
        self.check_columns_consistency()


        self.taboo_data_collector: dict = {
            'game': [],
            'game_id': [],
            'model': [],
            'benchmark_version': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat_p1': [],
            'chat_p2': [],
            'target_word': [],
            'related_words': [],
            'main_score': []
        }

        self.wordle_no_clue_no_critic_data_collector: dict = {
            'game': [],
            'game_id': [],
            'model': [],
            'benchmark_version': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat': [],
            'target_word': [],
            'target_word_difficulty': [],
            'target_word_clue': [],
            'main_score': []
        }

        self.wordle_with_clue_no_critic_data_collector: dict = {
            'game': [],
            'game_id': [],
            'model': [],
            'benchmark_version': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat': [],
            'target_word': [],
            'target_word_difficulty': [],
            'target_word_clue': [],
            'main_score': []
        }

        self.wordle_with_clue_with_critic_data_collector: dict = {
            'game': [],
            'benchmark_version': [],
            'game_id': [],
            'model': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat_p1': [],
            'chat_p2': [],
            'target_word': [],
            'target_word_difficulty': [],
            'main_score': []
        }

        self.referencegame_data_collector: dict = {
            'game': [],
            'benchmark_version': [],
            'game_id': [],
            'model': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat_p1': [],
            'chat_p2': [],
            'target_grid_name': [],
            'main_score': [],
            'request_count': [],
            'request_ratio': [],
            'average_expression_tokens': []
        }

        self.privateshared_data_collector: dict = {
            'game': [],
            'benchmark_version': [],
            'game_id': [],
            'model': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat_p1': [],
            'slots': [],
            'main_score': []
        }

        self.imagegame_data_collector: dict = {
            'game': [],
            'benchmark_version': [],
            'game_id': [],
            'model': [],
            'experiment': [],
            'episode': [],
            'Aborted': [],
            'Lose': [],
            'Success': [],
            'chat_p1': [],
            'chat_p2': [],
            'target_grid': [],
            'main_score': [],
            'request_count': [],
            'request_ratio': [],
            'average_expression_tokens': []
        }

        self.instance_data_extractors: dict = {
            'taboo': self.extract_taboo_interaction_data,
            'wordle': self.extract_wordle_no_clue_no_critic_data,
            'wordle_withclue': self.extract_wordle_no_clue_no_critic_data,
            'wordle_withcritic':  self.extract_wordle_clue_and_critic_data,
            'referencegame': self.extract_referencegame_data,
            'privateshared': self.extract_privateshared_data,
            'imagegame': self.extract_imagegame_data,
        }

        self.update_collector: dict = {
            'taboo': self.update_taboo_data_collector,
            'wordle': self.update_wordle_no_clue_no_critic_data_collector,
            'wordle_withclue': self.update_wordle_no_clue_no_critic_data_collector,
            'wordle_withcritic': self.update_wordle_clue_and_critic_data_collector,
            'referencegame': self.update_referencegame_data_collector,
            'privateshared': self.update_privateshared_data_collector,
            'imagegame': self.update_imagegame_data_collector,
        }
        
        self.data_collectors: dict = {
            'taboo': self.taboo_data_collector,
            'wordle': self.wordle_no_clue_no_critic_data_collector,
            'wordle_withclue': self.wordle_no_clue_no_critic_data_collector,
            'wordle_withcritic':  self.wordle_with_clue_with_critic_data_collector,
            'referencegame': self.referencegame_data_collector,
            'privateshared': self.privateshared_data_collector,
            'imagegame': self.imagegame_data_collector,
        }

    def prepare_raw_csv(self, data: pd.DataFrame, columns_to_keep: list[str]) -> pd.DataFrame:
        """
        This function transposes the raw csv data to have a column for each metric.
        The raw csv file has the following format:
        'game', 'model', 'experiment', 'episode', 'metric', 'value'

        every model, game, experiment, episode appears as often as there are metrics for a game instance.
        This function transforms every episode into one single line of a dataframe that has a column for each metric.

        Args:
            data: A Dataframe containing the raw data from raw.csv
            columns_to_keep: A list of all columns that are important to keep in the output dataframe

        Returns: Pivoted data frame that has a column for each metric containing the value for the metric or nan.
        """
        df: pd.DataFrame = data.pivot_table(
            index=['game', 'model', 'experiment', 'episode'],
            columns=['metric'],
            values='value'
        ).reset_index()

        columns_to_drop: list = [column for column in list(df.keys()) if column not in columns_to_keep]
        return df.drop(columns=columns_to_drop, axis=0)

    def prepare_instance_data(self, path: str) -> dict:
        """
        This function loads the instance.json file and returns it as a dictionary.
        Args:
            path: the path to the instance.json file

        Returns: Dictionary containing the instance data.
        """
        with open(path, 'r') as f:
            data: dict = json.load(f)
            return data

    def check_benchmark_version_consistency(self):
        """
        Ensure that only benchmark versions from the available options are chosen
        Returns: None

        """
        clean_benchmark_versions: list[str] = []
        for benchmark_version in self.benchmark_versions:
            if benchmark_version not in AVAILABLE_BENCHMARK_VERSIONS:
                print(f'Benchmark version {benchmark_version} is not available. Please chose only from {AVAILABLE_BENCHMARK_VERSIONS}')
            else:
                clean_benchmark_versions.append(benchmark_version)

        self.benchmark_versions = clean_benchmark_versions

    def check_games_consistency(self):
        """
        Ensure that only available games from the available options are chosen
        Returns:
        """
        clean_games_versions: list[str] = []
        for game in self.games_to_extract:
            if game not in AVAILABLE_GAMES:
                print(f'Game {game} is not available. Please chose only from {AVAILABLE_GAMES}')
            else:
                clean_games_versions.append(game)

        self.games_to_extract = clean_games_versions

    def check_columns_consistency(self):
        """
        Ensure that only available columns from the available options are chosen
        Returns:
        """
        clean_columns: list[str] = []
        for column in self.columns_to_keep:
            if column not in AVAILABLE_COLUMNS_TO_KEEP:
                print(f'Column {column} is not available. Please chose only from {AVAILABLE_COLUMNS_TO_KEEP}')
            else:
                clean_columns.append(column)

        self.columns_to_keep = clean_columns

    def create_output_dir(self, path: str):
        if os.path.isdir(path):
            print("DIRECTORY IS NOT EMPTY")
        else:
            os.makedirs(path)

    def extract_taboo_interaction_data(self, data: dict) -> dict:
        chat_p1: list = []
        chat_p2: list = []

        # loop over all turns
        for i, turn in enumerate(data['turns']):

            # loop over all actions inside one turn
            for action in turn:
                if action['to'] == 'Player 1' and action['from'] == 'GM' and action['action']['type'] == "send message":
                    chat_p1.append({'role': self.USER, 'content': action['action']['content']})
                elif action['to'] == 'Player 2' and action['from'] == 'GM' and action['action']['type'] == "send message":
                    chat_p2.append({'role': self.USER, 'content': action['action']['content']})
                elif action['to'] == 'GM' and action['from'] == 'Player 1' and action['action']['type'] == "get message":
                    chat_p1.append({'role': self.ASSISTANT, 'content': action['action']['content']})
                elif action['to'] == 'GM' and action['from'] == 'Player 2' and action['action']['type'] == "get message":
                    chat_p2.append({'role': self.ASSISTANT, 'content': action['action']['content']})

        return {'chat_p1': chat_p1, 'chat_p2': chat_p2}

    def update_taboo_data_collector(self, _data: dict, instance_data: dict, row: pd.DataFrame, game_data: dict, bv: str, score_data: dict) -> dict:
        # fill in the taboo specifics
        _data['game'].append(row.game)
        _data['game_id'].append(instance_data['game_id'])
        _data['model'].append(row.model)
        _data['benchmark_version'].append(bv)
        _data['experiment'].append(row.experiment)
        _data['episode'].append(row.episode)
        _data['Aborted'].append(row.Aborted)
        _data['Lose'].append(row.Lose)
        _data['Success'].append(row.Success)
        _data['chat_p1'].append(game_data['chat_p1'])
        _data['chat_p2'].append(game_data['chat_p2'])
        _data['target_word'].append(instance_data['target_word'])
        _data['related_words'].append(instance_data['related_word'])
        _data['main_score'].append(score_data["episode scores"]["Main Score"])
        return _data

    def extract_wordle_no_clue_no_critic_data(self, data: dict) -> dict:
        chat: list = []

        for i, turn in enumerate(data['turns']):
            for action in turn:
                if action['from'] == 'GM' and action['to'] == 'Player 1' and action['action']['type'] == "send message":
                    chat.append({'role': self.USER, 'content': action['action']['content'], 'has_error': False})
                if action['from'] == 'Player 1' and action['to'] == 'GM' and action['action']['type'] == "get message":
                    chat.append({'role': self.ASSISTANT, 'content': action['action']['content'], 'has_error': False})

                if  action['from'] == 'GM' and action['to'] == 'GM' and action['action']['type'] == "metadata":
                    try:
                        error: str = action['action']['game_info']['error']
                        if error:
                            chat[-1]['has_error'] = True
                    except KeyError:
                        pass

        return {'chat': chat}

    def update_wordle_no_clue_no_critic_data_collector(self, _data: dict, instance_data: dict, row: pd.DataFrame, game_data: dict, bv: str, score_data: dict) -> dict:
        _data['game'].append(row.game)
        _data['game_id'].append(instance_data['game_id'])
        _data['model'].append(row.model)
        _data['benchmark_version'].append(bv)
        _data['experiment'].append(row.experiment)
        _data['episode'].append(row.episode)
        _data['Aborted'].append(row.Aborted)
        _data['Lose'].append(row.Lose)
        _data['Success'].append(row.Success)
        _data['chat'].append(game_data['chat'])
        _data['target_word'].append(instance_data['target_word'])
        _data['target_word_difficulty'].append(instance_data['target_word_difficulty'])
        _data['target_word_clue'].append(instance_data['target_word_clue'])
        _data['main_score'].append(score_data["episode scores"]['Main Score'])

        return _data

    def extract_wordle_clue_and_critic_data(self, data: dict) -> dict:
        chat_p1: list = []
        chat_p2: list  = []

        last_inserted: str = ''

        for i, turn in enumerate(data['turns']):
            for action in turn:
                if action['action']['type'] == 'send message' and action['to'] == 'Player 2':
                    chat_p2.append( { 'role': self.USER,  'content': action['action']['content'], 'has_error': False })
                    last_inserted = 'Player 2'
                    continue

                if action['action']['type'] == 'get message' and action['from'] == 'Player 2':
                    chat_p2.append( {'role': self.ASSISTANT, 'content': action['action']['content'], 'has_error': False })
                    last_inserted = 'Player 2'
                    continue

                if action['action']['type'] == 'send message' and action['to'] == 'Player 1':
                    chat_p1.append( { 'role': self.USER,  'content': action['action']['content'], 'has_error': False })
                    last_inserted = 'Player 1'
                    continue

                if action['action']['type'] == 'get message' and action['from'] == 'Player 1':
                    chat_p1.append( { 'role': self.ASSISTANT,  'content': action['action']['content'], 'has_error': False})

                    last_inserted = 'Player 1'
                    continue

                if  action['from'] == 'GM' and action['to'] == 'GM' and action['action']['type'] == "metadata":
                    try:
                        error: str = action['action']['game_info']['error']
                        if error:
                            if last_inserted == 'Player 1':
                                chat_p1[-1]['has_error'] = True
                            else:
                                chat_p2[-1]['has_error'] = False
                    except KeyError:
                        pass

        return {'chat_p1': chat_p1, 'chat_p2': chat_p2}

    def update_wordle_clue_and_critic_data_collector(self, _data: dict, instance_data: dict, row: pd.DataFrame, game_data: dict, bv: str, score_data: dict) -> dict:
        _data['game'].append(row.game)
        _data['benchmark_version'].append(bv)
        _data['game_id'].append(instance_data['game_id'])
        _data['model'].append(row.model)
        _data['experiment'].append(row.experiment)
        _data['episode'].append(row.episode)
        _data['Aborted'].append(row.Aborted)
        _data['Lose'].append(row.Lose)
        _data['Success'].append(row.Success)
        _data['chat_p1'].append(game_data['chat_p1'])
        _data['chat_p2'].append(game_data['chat_p2'])
        _data['target_word'].append(instance_data['target_word'])
        _data['target_word_difficulty'].append(instance_data['target_word_difficulty'])
        _data['main_score'].append(score_data["episode scores"]['Main Score'])

        return _data

    def extract_referencegame_data(self, data: dict) -> dict:
        chat_p1: list = []
        chat_p2: list = []

        for turn in data['turns']:
            for action in turn:
                if action['to'] == 'Player 1':
                    chat_p1.append({
                        'role': self.USER,
                        'content': action['action']['content']
                    })
                if action['to'] == 'Player 2':
                    chat_p2.append({
                        'role': self.USER,
                        'content': action['action']['content']
                    })

                if action['from'] == 'Player 1':
                    chat_p1.append({
                        'role': self.ASSISTANT,
                        'content': action['action']['content']
                    })
                if action['from'] == 'Player 2':
                    chat_p2.append({
                        'role': self.ASSISTANT,
                        'content': action['action']['content']
                    })
        return {'chat_p1': chat_p1, 'chat_p2': chat_p2}

    def update_referencegame_data_collector(self, _data: dict, instance_data: dict, row: pd.DataFrame, game_data: dict, bv: str, score_data: dict) -> dict:
        _data['game'].append(row.game)
        _data['benchmark_version'].append(bv)
        _data['game_id'].append(instance_data['game_id'])
        _data['model'].append(row.model)
        _data['experiment'].append(row.experiment)
        _data['episode'].append(row.episode)
        _data['Aborted'].append(row.Aborted)
        _data['Lose'].append(row.Lose)
        _data['Success'].append(row.Success)
        _data['chat_p1'].append(game_data['chat_p1'])
        _data['chat_p2'].append(game_data['chat_p2'])
        _data['target_grid_name'].append(instance_data['target_grid_name'])
        _data['main_score'].append(score_data["episode scores"]['Main Score'])
        _data['request_count'].append(score_data["episode scores"]['Request Count'])
        _data['request_ratio'].append(score_data["episode scores"]['Request Success Ratio'])
        try:
            _data['average_expression_tokens'].append(score_data["episode scores"]['Average Generated Expression Number of Tokens'])
        except KeyError:
            _data['average_expression_tokens'].append(score_data["episode scores"]['Generated Expression Number of Tokens'])


        return _data

    def extract_privateshared_data(self, data: dict) -> dict:
        chat_p1: list = []

        for turn in data['turns']:
            for action in turn:
                if action['to'] == 'Player 1':
                    chat_p1.append({
                        'role': self.USER,
                        'content': action['action']['content'],
                        'type': action['action']['type'],
                    })

                if action['from'] == 'Player 1':
                    chat_p1.append({
                        'role': self.ASSISTANT,
                        'content': action['action']['content'],
                        'type': action['action']['type'],
                    })
        return {'chat_p1': chat_p1}

    def update_privateshared_data_collector(self, _data: dict, instance_data: dict, row: pd.DataFrame, game_data: dict, bv: str, score_data: dict) -> dict:
        _data['game'].append(row.game)
        _data['benchmark_version'].append(bv)
        _data['game_id'].append(instance_data['game_id'])
        _data['model'].append(row.model)
        _data['experiment'].append(row.experiment)
        _data['episode'].append(row.episode)
        _data['Aborted'].append(row.Aborted)
        _data['Lose'].append(row.Lose)
        _data['Success'].append(row.Success)
        _data['chat_p1'].append(game_data['chat_p1'])
        _data['slots'].append(instance_data['slots'])
        _data['main_score'].append(score_data["episode scores"]['Main Score'])

        return _data

    def extract_imagegame_data(self, data: dict) -> dict:
        chat_p1: list = []
        chat_p2: list = []

        for turn in data['turns']:
            for action in turn:
                if action['to'] == 'Player 1':
                    chat_p1.append({
                        'role': self.USER,
                        'content': action['action']['content'],
                    })
                if action['to'] == 'Player 2':
                    chat_p2.append({
                        'role': self.USER,
                        'content': action['action']['content'],
                    })

                if action['from'] == 'Player 1':
                    chat_p1.append({
                        'role': self.ASSISTANT,
                        'content': action['action']['content'],
                    })
                if action['from'] == 'Player 2':
                    chat_p2.append({
                        'role': self.ASSISTANT,
                        'content': action['action']['content'],
                    })

        return {'chat_p1': chat_p1, 'chat_p2': chat_p2}

    def update_imagegame_data_collector(self, _data: dict, instance_data: dict, row: pd.DataFrame, game_data: dict, bv: str, score_data: dict) -> dict:
        _data['game'].append(row.game)
        _data['benchmark_version'].append(bv)
        _data['game_id'].append(instance_data['game_id'])
        _data['model'].append(row.model)
        _data['experiment'].append(row.experiment)
        _data['episode'].append(row.episode)
        _data['Aborted'].append(row.Aborted)
        _data['Lose'].append(row.Lose)
        _data['Success'].append(row.Success)
        _data['chat_p1'].append(game_data['chat_p1'])
        _data['chat_p2'].append(game_data['chat_p2'])
        _data['target_grid'].append(instance_data['target_grid'])
        _data['main_score'].append(score_data["episode scores"]['Main Score'])
        _data['request_count'].append(score_data["episode scores"]['Request Count'])
        _data['request_ratio'].append(score_data["episode scores"]['Request Success Ratio'])
        _data['average_expression_tokens'].append(score_data["episode scores"]['Average Generated Expression Number of Tokens'])

        return _data

    def extract_data(self):
        self.print_statistics()
        for benchmark_version in self.benchmark_versions:
            print(f"Start Extracting Benchmark Data for Version {benchmark_version}")
            # read the raw_csv
            raw_csv_data: pd.DataFrame = pd.read_csv(f'./{benchmark_version}/raw.csv')

            # group by metric to obtain all episode information
            clean_csv_data: pd.DataFrame = self.prepare_raw_csv(data=raw_csv_data, columns_to_keep=self.columns_to_keep)

            # loop over all entries and build paths
            for index, row in clean_csv_data.iterrows():
                # built paths
                path_requests_json: str = f'./{benchmark_version}/{row.model}/{row.game}/{row.experiment}/{row.episode}/requests.json'
                path_instance_json: str = f'./{benchmark_version}/{row.model}/{row.game}/{row.experiment}/{row.episode}/instance.json'
                path_interaction_json: str = f'./{benchmark_version}/{row.model}/{row.game}/{row.experiment}/{row.episode}/interactions.json'
                path_scores_json: str = f'./{benchmark_version}/{row.model}/{row.game}/{row.experiment}/{row.episode}/scores.json'

                # skip games that are not needed to be extracted
                if row['game'] not in self.games_to_extract:
                    continue

                # check that paths are correctly built
                try:
                    assert os.path.isfile(path_requests_json)
                    assert os.path.isfile(path_instance_json)
                    assert os.path.isfile(path_interaction_json)
                    assert os.path.isfile(path_scores_json)
                except AssertionError:
                    print('assertion error in version', benchmark_version, ' on path_instance_json', path_instance_json, ' on path_requests_json', path_requests_json)
                    continue

                instance_data: dict = self.prepare_instance_data(path=path_instance_json)
                score_data: dict = self.prepare_instance_data(path=path_scores_json)

                try:
                    interaction_data: dict = self.prepare_instance_data(path=path_interaction_json)
                except JSONDecodeError as e:
                    print(e)
                    print(path_instance_json)
                    continue

                # get the data collector
                data_collector: dict = self.data_collectors[row.game]

                if not data_collector:
                    print(row.game)

                # extract the game data
                game_data: dict = self.instance_data_extractors[row.game](data=interaction_data)

                # add data to the data collector
                self.data_collectors[row.game] = self.update_collector[row.game](_data=data_collector, instance_data=instance_data, row=row, game_data=game_data, bv=benchmark_version, score_data=score_data)

    def save_data(self):
        for key in self.data_collectors.keys():
            if key not in self.games_to_extract:
                continue
            save_dir: str = self.output_dir + f'/{key}_raw.jsonl'
            df: pd.DataFrame = pd.DataFrame(data=self.data_collectors[key])
            df.to_json(save_dir, orient='records', lines=True)

    def print_statistics(self):
        print(f"Extracting game data from following games: {self.games_to_extract}")
        print(f"Extracting data from following benchmark versions: {self.benchmark_versions}")
        print(f"Saving data to following path: {self.output_dir}")


if __name__ == '__main__':
    extractor = DataExtractor()
    extractor.extract_data()
    extractor.save_data()