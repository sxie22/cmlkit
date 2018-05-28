import numpy as np


def log2(start, stop, n):
    """Generate a 1-d grid in base 2 logspace."""

    return np.logspace(start, stop, num=n, base=2.0)
