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
    return parse.nested_to_smt(substitute_special_names(str(nested_string)))


def compute_wmi(domain, queries, formula=None, weight_function=None):
    if formula is None:
        formula = smt.TRUE()

    if weight_function is None:
        weight_function = smt.Real(1.0)

    support = []
    for v in domain.real_vars:
        lb, ub = domain.var_domains[v]
        sym = smt.Symbol(substitute_special_names(v), domain.var_types[v])
        support.append(lb <= sym)
        support.append(sym <= ub)
    formula = smt.simplify(smt.And(formula, *support))

    wmi = WMI()
    total_volume, _ = wmi.compute(formula, weight_function, WMI.MODE_PA)
    for query in queries:
        query_volume, _ = wmi.compute(formula & query, weight_function, WMI.MODE_PA)
        yield query_volume / total_volume


def run(flat):
    """
    Computes the WMI using JSON input
    :param flat: A dict containing the string encoded domain, query / queries and optional formula and weight function
    :return:
    """
    domain = problem.import_domain(flat["domain"])

    if "formula" in flat:
        formula = convert(flat["formula"])
    else:
        formula = smt.TRUE()

    if "weights" in flat:
        weights = convert(flat["weights"])
    else:
        weights = smt.Real(1.0)

    if "query" in flat:
        queries = [convert(flat["query"])]
    elif "queries" in flat:
        queries = [convert(query_string) for query_string in flat["queries"]]
    else:
        print("No queries or tasks detected.")
        return

    i = 0
    for p in compute_wmi(domain, queries, formula, weights):
        i += 1
        print("p(q{}): {}".format(i, p))


if __name__ == "__main__":
    def _parse():
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--filename", default=None)
        parser.add_argument("-s", "--json_string", default=None)

        args = parser.parse_args()
        if args.filename is not None:
            with open(args.filename) as f:
                flat = json.load(f)
        elif args.json_string is not None:
            flat = json.loads(args.json_string)
        else:
            raise RuntimeError("No input provided")
        run(flat)

    _parse()
