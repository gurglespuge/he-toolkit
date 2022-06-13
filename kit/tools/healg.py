# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""This module finds HE parameters based on user constraints"""

import math
import re
import shutil
from argparse import ArgumentTypeError
from subprocess import CalledProcessError, run, PIPE
from sys import stdout, stderr, exit as sys_exit
from itertools import chain, combinations
from collections import Counter
from pathlib import Path
from typing import List, Iterable


def set_gen_primes_subparser(subparsers):
    """Register subparser to generate primes"""

    parser = subparsers.add_parser(
        "gen-primes",
        description="generate primes in range [n, m] where n, m are positive integers",
    )
    parser.add_argument("start", type=int, default=2, help="start number")
    parser.add_argument("stop", type=int, default=100, help="stop number")
    parser.set_defaults(fn=lambda args: gen_primes(args.start, args.stop))


def gen_primes(start: int, stop: int, outfile=stdout):
    """Writes to outfile a list of primes from start to stop values inclusive"""

    numbers = range(start, stop + 1)
    primes = [
        factors[0] for factors in compute_prime_factors(numbers) if len(factors) == 1
    ]
    print("\n".join(map(str, primes)), file=outfile)


def powerset(iterable):
    """Returns a generator.
       Note that we do not return the empty set.
       https://docs.python.org/3/library/itertools.html"""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(1, len(s) + 1))


def find_ms(ps, ds, factorize, m_max):
    """Generator returns the p, gen for max m's for p^d"""
    prime_factors = factorize((p ** d - 1 for p in ps for d in ds), m_max)
    if prime_factors:
        all_factors = tuple(powerset(primes) for primes in prime_factors)
        pd = ((p, d) for p in ps for d in ds)
        for (p, d), ms in zip(pd, all_factors):
            for m_factors in ms:
                m = math.prod(m_factors)
                if m_max is None or m <= m_max:
                    yield p, d, m, m_factors


def str_to_range(s):
    """Parse a string and return a Python range object.
       This function expects a positive integer."""
    if s.isdigit():
        num = int(s)
        return range(num, num + 1)

    regex = re.compile(r"^((\d+)\s*-\s*(\d+))$")
    match = None
    try:
        match, start, end = regex.fullmatch(s).groups()
        if match is None:
            raise ArgumentTypeError(f"Unknown error. Range with match '{match}'")
        start, end = int(start), int(end)
        if start > end:
            raise ArgumentTypeError(f"backward range '{match}'")
        return range(start, end + 1)
    except AttributeError as error:
        if match:
            raise ArgumentTypeError(
                f"Wrong syntax for range given '{match}'."
            ) from error
        raise ArgumentTypeError(f"Wrong syntax for range given '{s}'.") from error


def parse_range(string, filter_fn=None):
    """Returns sorted list"""
    ranges = (str_to_range(s) for s in string.replace(" ", "").split(","))

    if filter_fn is None:
        unique_nums = {x for r in ranges for x in r}
    else:
        unique_nums = {x for r in ranges for x in r if filter_fn(x)}

    return sorted(unique_nums)


def parse_range_for_primes(string):
    """Create a file with sorted primes"""
    default_primes_filepath = Path("~/.hekit/primes.txt").expanduser()
    try:
        primes_list = PrimesFromFile(default_primes_filepath)
    except FileNotFoundError:
        with default_primes_filepath.open("a", encoding="utf-8") as f:
            gen_primes(2, 140_000, outfile=f)
            gen_primes(140_001, 180_000, outfile=f)
        primes_list = PrimesFromFile(default_primes_filepath)

    return parse_range(string, filter_fn=primes_list.is_prime)


class PrimesFromFile:
    """Process primes from a text file."""

    def __init__(self, filename):
        """Load file with primes."""
        with open(filename, encoding="utf-8") as f:
            self.primes = tuple(int(p) for p in f.readlines())
            self.max = self.primes[-1]

    def is_prime(self, n):
        """Return True if prime for numbers upto numbers in the file."""
        if n > self.max:
            raise ValueError(f"Cannot process number higher than {self.max}")
        return n in self.primes


def parse_factor_line(line):
    """ 'num: f1 f2 f3' -> (num, (f1, f2, f3))"""
    split_line = line.split()  # ['key:', 'v1', 'v2' , ...]
    key = split_line[0]
    if key[-1] != ":":
        raise ValueError(f"{line} does not have valid key format")
    key = int(key[:-1])
    value = tuple(int(num) for num in split_line[1:])
    return key, value


def compute_prime_factors(numbers, factor_util="factor"):
    """Return generator. Keys m, Value prime factors.
       Process out to factor"""

    numbers = list(numbers)
    if len(numbers) == 0:
        return None

    command_and_args = [factor_util, *map(str, numbers)]

    try:
        out = run(command_and_args, stdout=PIPE, check=True)
    except CalledProcessError as error:
        # Was it a negative number on the input?
        if any(number < 0 for number in numbers):
            raise ValueError(
                f"A negative number was found in the input: {numbers}"
            ) from error
        raise error

    factor_lines = out.stdout.decode("ascii").strip().split("\n")

    # We only want the value a.k.a. the primes factors
    # A generator here does not save memory, but makes the parsing lazy
    return (parse_factor_line(line)[1] for line in factor_lines)


def compute_prime_factors_by_part_lookup(numbers: Iterable[int], m_max) -> List[int]:

    # Code duplication
    default_primes_filepath = Path("~/.hekit/primes.txt").expanduser()
    try:
        primes = PrimesFromFile(default_primes_filepath)
    except FileNotFoundError:
        #        with default_primes_filepath.open("a", encoding="utf-8") as f:
        #            gen_primes(2, 140_000, outfile=f)
        #            gen_primes(140_001, 150_000, outfile=f)
        primes = PrimesFromFile(default_primes_filepath)

    numbers = list(numbers)
    for rem in numbers:
        p_factors = []
        for p in primes.primes:
            if m_max is not None and p > m_max:
                skip_normal = True
                continue
            while rem != 1 and rem % p == 0:
                p_factors.append(p)
                rem //= p

        if skip_normal is True:
            yield tuple(p_factors)
        else:
            # FIXME compute_prime_factors will thrash IO like this
            # pass leftovers to normal factorize program
            rem_factors = next(compute_prime_factors([rem]))
            yield tuple(p_factors) + rem_factors


def set_gen_algebras_subparser(subparsers):
    """Register subparser to generate algebras"""
    parser = subparsers.add_parser(
        "algebras", description="generate ZZ_p[x]/phi(X) algebras"
    )

    parser.add_argument(
        "-p", type=parse_range_for_primes, default="2", help="plaintext prime"
    )
    parser.add_argument(
        "-d", type=parse_range, default="1", help="number of coefficients in a slot"
    )
    parser.add_argument("--m-max", type=int, help="max m")
    parser.add_argument(
        "--part-lookup",
        action="store_true",
        help="when factoring initially use a lookup table",
    )
    parser.add_argument(
        "--no-corrected", action="store_false", help="include corrected d orders"
    )
    parser.add_argument(
        "--no-header", action="store_false", help="do not print headers"
    )

    factor_util = shutil.which("factor") or shutil.which("gfactor")
    if factor_util is None:
        print("To run, factor utility is required.", file=stderr)
        sys_exit(1)

    parser.set_defaults(fn=healg, factor_util=factor_util)


def phi(prime_factors):
    """"Euler's totient from prime factors.
        This function assumes that only primes are passed in."""
    c = Counter(prime_factors)
    return math.prod((p - 1) * p ** (k - 1) for p, k in c.items())


def correct_for_d(p, d, m):
    """Returns the minimum value of d satisfiying p^d = 1 mod m.
    Computations for valid ms with a starting point of p^d can
    sometimes lead to an erroneous d.

    This function expects that p is a prime number."""
    for e in range(1, d + 1):
        if (p ** e) % m == 1:
            break

    return e, e != d


def healg(args):
    """Given a prime p(s) and a required d(s) what algebras (p, d, m)
    are available?"""

    # Sanity check that we have at least one prime to work with
    if not args.p:
        print("prime p not found in numbers provided", file=stderr)
        sys_exit(1)

    solns = set()
    width = 20
    if args.no_header:
        print(
            f"{'p' :^{width}} {'d' :^{width}} {'m' :^{width}} {'phim' :^{width}} {'nslots' :^{width}}"
        )
    factorize_function = (
        compute_prime_factors_by_part_lookup
        if args.part_lookup
        else compute_prime_factors
    )
    for p, d, m, m_factors in find_ms(args.p, args.d, factorize_function, args.m_max):
        e, corrected = correct_for_d(p, d, m)
        soln = (p, e, m)
        if soln not in solns:
            solns.add(soln)
            if not args.no_corrected and corrected:
                continue
            phim = phi(m_factors)
            print(
                f"{p :^{width}} {e :^{width}} {m :^{width}} {phim :^{width}} {phim // e :^{width}}"
            )

    if args.no_header:
        print(
            f"{'p' :^{width}} {'d' :^{width}} {'m' :^{width}} {'phim' :^{width}} {'nslots' :^{width}}"
        )
