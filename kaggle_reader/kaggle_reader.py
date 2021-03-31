"""
    This module generates plots on statistic extracted from the csv file which can be found at:
    https://www.kaggle.com/martj42/international-football-results-from-1872-to-2017
"""

__license__ = "Riccardo-Cereghino-4651066|Stefano-Mule-4671228"
__docformat__ = 'reStructuredText'

import operator
import os
from functools import reduce
from typing import List, Iterator, Dict, Any, Tuple, Callable, Union


def selector(el: Dict[str, Any], mode: str, operators: List[Tuple[Callable, str, Any]]) -> bool:
    """
    Given a List of comparisons (operators, ex: x < 3) returns a boolean expressing a simple logic port for all
    operators, it is used in :func:`select`
    """
    result = False if mode == 'or' else True

    for op, k, v in operators:
        _result = op(el.get(k), v)

        if mode == 'or':
            result = _result or result
        else:
            result = _result and result
    return result


def operators_reader(**kwargs: Union[str, Any]) -> List[Tuple[Callable, str, Any]]:
    """
    Given any number of kwargs in the form:
    - input is in the form::

        team_name__eq="Italy"
        avg_goals_scored__gte=1

    It returns a list of functions from the operator library, based on the *__eq* section of the kwargs keyword.

    The arguments of the operator function will be, on the left, the value of the key of the yielded dict and on the
    right the value od the key of the corresponding kwargs value.

    It is used in :func:`select`.
    """
    operators = []
    for kw in kwargs:
        if '__' in kw:
            _kw, op = kw.split('__')
            # only allow valid operators
            if op not in ('lt', 'le', 'eq', 'ne', 'ge', 'gt'):
                raise Exception("Invalid Operator")
        else:
            op = 'eq'
            _kw = kw

        _operator = getattr(operator, op)

        operators.append((_operator, _kw, kwargs[kw]))

    return operators


def select(it: Iterator[Dict[str, Any]], **kwargs) -> Iterator[dict[str, Any]]:
    """
    Given a dict iterator (it) and any number of kwargs,
    - in the form::

        team_name__eq="Italy"
        avg_goals_scored__gte=1

    Returns a :func:`filter` iterator, filtering based on the condition specified in kwargs`.
    """
    mode = kwargs.pop('mode', 'or')
    operators = operators_reader(**kwargs)

    return filter(lambda el: selector(el, mode, operators), it)


def row_splitter(row: str) -> List[str]:
    """Given a string returns a csv row, splits the cells into elements of a list

    - input is in the form::
          row = "a,b,c\\n"
    """
    return row[:-1].split(',')


def csv_reader(file_name: str) -> Iterator[str]:
    """Generates an iterator per line from a file encoded in utf8, specified with file_name"""
    for line in open(file_name, "r", encoding="utf8"):
        yield line


def generate_games(file: str) -> Iterator[Dict[str, str]]:
    """
    Iterates through a csv file (path), picks the first line to be used
    as keys for the yielded list of returning dict
    """
    csv_gen = csv_reader(file)

    columns = row_splitter(next(csv_gen))

    for row in csv_gen:
        yield dict(zip(columns, row_splitter(row)))


def team_goals(game: dict[str, Any], team_name: str):
    if game['home_team'] == team_name:
        return int(game['home_score'])
    return int(game['away_score'])


def sum_goals(games: Iterator[dict[str, Any]], team_name: str) -> int:
    return reduce(lambda res, game: res + team_goals(game, team_name), games, 0)


if __name__ == '__main__':
    games_generator = generate_games(os.path.abspath('csv/results.csv'))

    team = "Italy"
    print("Italy games")

    try:
        search_params = {
            "tournament__eq": "FIFA World Cup"
        }

        tournament = select(games_generator, **search_params)

        search_params = {
            "mode": "or",
            "home_team__eq": team,
            "away_team__e": team
        }

        print(sum_goals(select(tournament, **search_params), team))
    except Exception as ex:
        print(ex)
