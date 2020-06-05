import numpy as np
from pathlib import Path

from cmlkit.engine.config import Configurable
from cmlkit.engine.inout import normalize_extension
from cmlkit.engine.hashing import compute_hash


class Data(Configurable):

    kind = "data"  # subclasses must change this

    def __init__(self, data, info, meta, context={}):
        super().__init__()
        self.data = data
        self.info = info
        self.meta = meta

    @classmethod
    def create(cls, data=None, info=None, history=None):
        if history is None:
            if data is None:
                history = [f"{cls.kind}@{compute_hash(np.random.random())}"]
            else:
                history = [f"{cls.kind}@{compute_hash(**data)}"]

        if data is None:
            data = {}

        if info is None:
            info = {}

        meta = {"history": history}

        return cls(data, info, meta)

    @classmethod
    def result(cls, component, input_data, data=None, info=None):
        """Create new Data instance as result of applying component to input"""

        new_history = input_data.history.copy()
        new_history.append(component.get_hid())

        return cls.create(data=data, info=info, history=new_history)

    def _get_config(self):
        return {"data": self.data, "info": self.info, "meta": self.meta}

    def dump(self, path, protocol=1):
        assert protocol == 1, "Data only supports protocol 1 (.npz)"

        write_data_npz(path, self.kind, self.data, self.info, self.meta)


    @property
    def id(self):
        return compute_hash(self.history)

    @property
    def history(self):
        return self.meta["history"]


def load_data(path):
    path = Path(path)

    if path.suffix == ".npz":
        return load_data_npz(path)
    else:
        raise ValueError


def load_data_npz(path):

    with np.load(path, allow_pickle=True) as file:
        protocol = file["protocol"].item()
        assert protocol == 1, "npz data should be protocol 1"

        kind = file["kind"].item()
        meta = file["meta"].item()
        info = file["info"].item()

        data = {}
        for name, array in file.items():
            if name.split("/")[0] == "data":
                data[name.split("/")[1]] = array

        config = {kind: {"info": info, "data": data, "meta": meta}}

    from cmlkit import from_config

    return from_config(config)


def write_data_npz(path, kind, data, info, meta):
    kwds = {"kind": kind, "info": info, "meta": meta, "protocol": 1}

    for name, array in data.items():
        kwds[f"data/{name}"] = array

    np.savez(normalize_extension(path, ".npz"), **kwds)
