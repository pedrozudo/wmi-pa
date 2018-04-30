from __future__ import print_function, division

import json
import argparse

import os
import random
import string

import math
import pysmt.shortcuts as smt

from sys import path

import re
import problem
import parse

path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
from wmi import WMI
import wmiinference
from weights import Weights
from wmiinference import WMIInference


def substitute_special_names(nested_string):
    replacement = "_symbol"
    return re.sub("pi", "pi{}".format(replacement), nested_string)


def convert(nested_string):
    return parse.nested_to_smt(substitute_special_names(str(nested_string)))


def clean(symbols, domain, queries, formula, weight_function):
    mapping = dict()
    names = set()

    n = max(2, int(math.ceil(len(domain.variables) / len(string.ascii_lowercase))))
    for var in domain.variables:
        new_name = None
        while new_name is None or new_name in names or new_name == "pi":
            new_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(n))
        names.add(new_name)
        mapping[var] = new_name

    adapted_domain = problem.Domain(
        [mapping[v] for v in domain.variables],
        {mapping[v]: domain.var_types[v] for v in domain.var_types.keys()},
        {mapping[v]: domain.var_domains[v] for v in domain.var_domains.keys()},
    )

    substitution = {symbols[v]: adapted_domain.get_symbol(mapping[v]) for v in domain.variables}
    adapted_queries = [smt.substitute(query, substitution) for query in queries ]
    adapted_formula = smt.substitute(formula, substitution)
    adapted_weight_function = smt.substitute(weight_function, substitution)
    return adapted_domain, adapted_queries, adapted_formula, adapted_weight_function


def compute_wmi(domain, queries, formula=None, weight_function=None):
    if formula is None:
        formula = smt.TRUE()

    if weight_function is None:
        weight_function = smt.Real(1.0)

    symbols = {v: domain.get_symbol(v) for v in domain.variables}

    domain, queries, formula, weight_function = clean(symbols, domain, queries, formula, weight_function)

    support = []
    for v in domain.real_vars:
        lb, ub = domain.var_domains[v]
        sym = domain.get_symbol(v)
        support.append(lb <= sym)
        support.append(sym <= ub)
    formula = smt.simplify(smt.And(formula, *support))

    # wmi = WMI()
    engine = WMIInference(formula, weight_function)

    # weights = Weights(weight_function)
    # bool_symbols = [domain.get_symbol(v) for v in domain.bool_vars]
    # total_volume, _ = wmi.compute(formula, weight_function, WMI.MODE_PA, set(bool_symbols))
    for query in queries:
        # query_volume, _ = wmi.compute(formula & query, weight_function, WMI.MODE_PA, bool_symbols)
        # yield query_volume / total_volume
        yield engine.compute_normalized_probability(query)


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
