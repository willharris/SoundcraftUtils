#!/usr/bin/env python3
from argparse import ArgumentParser

import json

cmd = {
    "s": {
        "cmd": "swap",
        "help": "swap the two channels",
        "args": 2
    }
}


class Mixer:

    def __init__(self, config) -> None:
        self.config = config
        data = json.loads(self.config)

        nested_data = {}
        for k, v in data.items():
            keys = k.split(".")
            self.nest_data(nested_data, keys, v)

        print(json.dumps(nested_data, indent=2))

    def nest_data(self, data, keys, val):
        key = keys.pop(0)
        if not keys:
            data[key] = val
        else:
            child = data[key] if key in data else {}
            data[key] = self.nest_data(child, keys, val)

        return data


def get_command():
    pass


if __name__ == "__main__":
    parser = ArgumentParser(description="Soundcraft Ui24r Mixer Utility")
    parser.add_argument(dest="config",
                        help="Input mixer configuration JSON")
    args = parser.parse_args()

    with open(args.config, "r") as config:
        mixer = Mixer(config.read())
