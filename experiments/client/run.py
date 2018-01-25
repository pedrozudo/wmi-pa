from __future__ import print_function, division

import json
import argparse

import os
import pysmt.shortcuts as smt

from sys import path

import re
import problem
import parse

path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
from wmi import WMI


def substitute_special_names(nested_string):
    replacement = "_symbol"
    return re.sub("pi", "pi{}".format(replacement), nested_string)


def convert(nested_string):
    return parse.nested_to_smt(substitute_special_names(nested_string))


def run(filename):
    """

    :param filename: The filename containing the problem, queries and weight function
    :return:
    """
    with open(filename) as f:
        flat = json.load(f)

    domain = problem.import_domain(flat["domain"])

    if "formula" in flat:
        formula = convert(flat["formula"])
    else:
        formula = smt.TRUE()

    support = []
    for v in domain.real_vars:
        lb, ub = domain.var_domains[v]
        sym = smt.Symbol(substitute_special_names(v), domain.var_types[v])
        support.append(lb <= sym)
        support.append(sym <= ub)
    formula = smt.simplify(smt.And(formula, *support))

    if "weights" in flat:
        weights = convert(flat["weights"])
    else:
        weights = smt.Real(1.0)

    if "query" in flat:
        query = convert(flat["query"])
        wmi = WMI()
        total_volume, _ = wmi.compute(formula, weights, WMI.MODE_PA)
        query_volume, _ = wmi.compute(formula & query, weights, WMI.MODE_PA)
        print(query_volume / total_volume)
    else:
        print("No queries or tasks detected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    run(args.filename)
