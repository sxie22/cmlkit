import os
import sys
from cmlkit.mbtr.mbtr import MBTR
import cmlkit.mbtr.funcs as uncached
from cmlkit.utils.caching import _diskcached, memcached
from cmlkit.inout import makedir


# In-memory cache size
if 'CML_CACHE_SIZE' in os.environ:
    cache_size = int(os.environ['CML_CACHE_SIZE'])
else:
    cache_size = 500

# Location for disk-backed cache
# Note that this will not be automatically cleared
if 'CML_CACHE_LOC' in os.environ:
    cache_loc = str(os.environ['CML_CACHE_LOC'])
else:
    # default to current running path of the script
    cache_loc = os.environ['PWD'] + '/cache'

makedir(cache_loc)


@memcached(max_entries=cache_size)
def explicit_single_mbtr_with_norm(*args):
    return uncached.explicit_single_mbtr_with_norm(*args, mbtr_gen=explicit_single_mbtr)


explicit_single_mbtr = _diskcached(uncached.explicit_single_mbtr, cache_location=cache_loc, name='explicit_single_mbtr')


def single_mbtr(*args):
    return uncached.single_mbtr(*args, mbtr_gen=explicit_single_mbtr_with_norm)


def make_mbtrs(*args):
    return uncached.make_mbtrs(*args, mbtr_gen=single_mbtr)


class DiskAndMemCachedMBTR(MBTR):
    """Cached version of MBTR, caching to disk and in memory

    The generation of MBTRs is cached twice: Single MBTRs without the norm are
    saved to disk in the folder specified by $CML_CACHE_LOC. MBTRs with norm
    are also saved in memory, with the cache size specified by
    $CML_CACHE_SIZE.

    """

    def _make_mbtr(self, dataset, spec):
        return make_mbtrs(dataset, spec)
