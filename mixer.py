#!/usr/bin/env python3
import json
import os

from argparse import ArgumentParser
from webbrowser import get


cmds = {
    "da": {
        "func": "dump_aux",
        "help": "dump the nested json for an aux channel",
        "args": ["channel"]
    },
    "di": {
        "func": "dump_input",
        "help": "dump the nested json for an input channel",
        "args": ["channel"]
    },
    "pa": {
        "func": "print_auxes",
        "help": "print the aux channels",
        "args": []
    },
    "pi": {
        "func": "print_inputs",
        "help": "print the input channels",
        "args": []
    },
    "r": {
        "func": "rename_input",
        "help": "rename the input channel",
        "args": ["channel", "name"]
    },
    "sa": {
        "func": "swap_auxes",
        "help": "swap two aux channels",
        "args": ["src", "dest"]
    },
    "si": {
        "func": "swap_inputs",
        "help": "swap two input channels",
        "args": ["src", "dest"]
    },
    "w": {
        "func": "write_file",
        "help": "write configuration to file",
        "args": ["filename"]
    },
    "q": {
        "func": "quit",
        "help": "quit (also: ctrl-d)",
        "args": []
    }
}


class Mixer:

    def __init__(self, config) -> None:
        self.config = config
        data = json.loads(self.config)
        if data["schema"] != "6":
            raise Exception(f"Unhandled schema version: {data['schema']}")

        nested_data = {}
        for k, v in data.items():
            keys = k.split(".")
            self._nest_data(nested_data, keys, v)

        self.data = nested_data

    def _nest_data(self, data: dict, keys: list, val: any) -> dict:
        key = keys.pop(0)
        child = data[key] if key in data else {}
        if not keys:
            if child:
                child["_"] = val
                data[key] = child
            else:
                data[key] = val
        else:
            if type(child) is not dict:
                child = {
                    "_": child
                }
            data[key] = self._nest_data(child, keys, val)

        return data

    def _check_stereo_pairs(self) -> bool:
        good = True
        for chan, data in sorted(self.data["i"].items()):
            if data["stereoIndex"] == 0:
                pair = str(int(chan) + 1)
                if pair not in self.data["i"] or self.data["i"][pair]["stereoIndex"] != 1:
                    print(f"Input channel {chan} ({data['name']}) is Stereo L but channel {pair} is not Stereo R")
                    good = False
                    break
            elif data["stereoIndex"] == 1:
                pair = str(int(chan) - 1)
                if pair not in self.data["i"] or self.data["i"][pair]["stereoIndex"] != 0:
                    print(f"Input channel {chan} ({data['name']}) is Stereo R but channel {pair} is not Stereo L")
                    good = False
                    break

        if good:
            for aux, data in sorted(self.data["a"].items()):
                if data["stereoIndex"] == 0:
                    pair = str(int(aux) + 1)
                    if pair not in self.data["a"] or self.data["a"][pair]["stereoIndex"] != 1:
                        print(f"Aux channel {aux} ({data['name']}) is Stereo L but channel {pair} is not Stereo R")
                        good = False
                        break
                elif data["stereoIndex"] == 1:
                    pair = str(int(aux) - 1)
                    if pair not in self.data["a"] or self.data["a"][pair]["stereoIndex"] != 0:
                        print(f"Aux channel {aux} ({data['name']}) is Stereo R but channel {pair} is not Stereo L")
                        good = False
                        break

        return good

    def _do_swap_viewgroups(self, a: int, b: int) -> None:
        # adapt viewgroup channels
        for vg, val in self.data["vg"].items():
            chans = json.loads(val["_"])
            idx_a = -1
            idx_b = -1
            try:
                idx_a = chans.index(a)
            except ValueError:
                pass
                
            try:
                idx_b = chans.index(b)
            except ValueError:
                pass

            if idx_a > -1:
                chans[idx_a] = b

            if idx_b > -1:
                chans[idx_b] = a

            val["_"] = json.dumps(chans).replace(" ", "")

        # adapt local channels
        for vg in self.data["LOCAL"]["viewGroups"]:
            idx_a = -1
            idx_b = -1
            try:
                idx_a = vg.index(a)
            except ValueError:
                pass
                
            try:
                idx_b = vg.index(b)
            except ValueError:
                pass

            if idx_a > -1:
                vg[idx_a] = b

            if idx_b > -1:
                vg[idx_b] = a

    def _do_swap_auxes(self, a: str, b: str) -> None:
        for chan in [a, b]:
            if chan not in self.data["a"]:
                print(f"Could not find aux channel {chan} for swapping")
                return

        # swap the actual aux channels
        tmp = self.data["a"][a]
        self.data["a"][a] = self.data["a"][b]
        self.data["a"][b] = tmp

        # swap the various "x" channel aux settings
        for chan_type in ["f", "i", "l", "p"]:
            for data in self.data[chan_type].values():
                tmp = data["aux"][a]
                data["aux"][a] = data["aux"][b]
                data["aux"][b] = tmp

        # Aux viewgroup indices start at 38
        self._do_swap_viewgroups(int(a) + 38, int(b) + 38)

    def _do_swap_inputs(self, a: str, b: str) -> None:
        for chan in [a, b]:
            if chan not in self.data["i"]:
                print(f"Could not find input channel {chan} for swapping")
                return

        # swap the actual channels
        tmp = self.data["i"][a]
        self.data["i"][a] = self.data["i"][b]
        self.data["i"][b] = tmp

        # adapt the hardware and "ua"(?) channels
        self.data["i"][a]["scsrc"] = f"ua.{a}"
        self.data["i"][a]["src"] = f"hw.{a}"
        self.data["i"][b]["scsrc"] = f"ua.{b}"
        self.data["i"][b]["src"] = f"hw.{b}"

        self._do_swap_viewgroups(int(a), int(b))

    def _flatten_data(self, flat_data: dict, key: str, data: dict) -> None:
        for k, v in data.items():
            # special case
            if k == "LOCAL":
                flat_data[k] = v
            else:
                if k == "_":
                    new_key = key
                else:
                    new_key = f"{key}.{k}" if key else k
                if type(v) is dict:
                    self._flatten_data(flat_data, new_key, v)
                else:
                    flat_data[new_key] = v

    #
    # Public methods
    #

    def dump_aux(self, aux: str) -> None:
        if aux not in self.data["a"]:
            print(f"Aux {aux} does not exist")
            return
        print(json.dumps(self.data["a"][aux], indent=2, sort_keys=True))

    def dump_input(self, input: str) -> None:
        if input not in self.data["i"]:
            print(f"Input {input} does not exist")
            return
        print(json.dumps(self.data["i"][input], indent=2, sort_keys=True))

    def print_auxes(self) -> None:
        for a in sorted(self.data["a"].keys(), key=lambda x: int(x)):
            stereo = ""
            if int(self.data["a"][a]["stereoIndex"]) == 0:
                stereo = "Stereo L"
            elif int(self.data["a"][a]["stereoIndex"]) == 1:
                stereo = "Stereo R"

            print("%2d: %s %s" % (
                int(a),
                self.data["a"][a]["name"],
                f"[{stereo}]" if stereo else ""
            ))

    def print_inputs(self) -> None:
        for i in sorted(self.data["i"].keys(), key=lambda x: int(x)):
            stereo = ""
            if int(self.data["i"][i]["stereoIndex"]) == 0:
                stereo = "Stereo L"
            elif int(self.data["i"][i]["stereoIndex"]) == 1:
                stereo = "Stereo R"
            print("%2d: %s %s" % (
                int(i),
                self.data["i"][i]["name"],
                f"[{stereo}]" if stereo else ""
            ))

    def rename_input(self, channel: str, name: str) -> None:
        if channel not in self.data["i"]:
            print(f"Input {input} does not exist")
            return

        old_name = self.data["i"][channel]["name"]
        name = name.replace("-", " ")
        self.data["i"][channel]["name"] = name

        print(f"Renamed input {channel} from {old_name} to {name}")

        self.print_inputs()

    def swap_auxes(self, src: str, dest: str) -> None:
        self._do_swap_auxes(src, dest)
        print(f"Swapped aux channel {src} with channel {dest}")

        self.print_auxes()

    def swap_inputs(self, src: str, dest: str) -> None:
        self._do_swap_inputs(src, dest)
        print(f"Swapped input channel {src} with channel {dest}")

        self.print_inputs()

    def write_file(self, dest: str) -> None:
        if not self._check_stereo_pairs():
            print("Invalid stereo pairs, won't write")
            return

        if os.path.exists(dest):
            print(f"File {dest} already exists.")
            overwrite = input("Overwrite? (y/N) ")
            if overwrite.lower() != "y":
                print("Not overwriting")
                return
            else:
                print("Overwriting")

        flat_data = {}
        self._flatten_data(flat_data, "", self.data)
        with open(dest, "w") as out:
            out.write(json.dumps(
                flat_data, indent=2, sort_keys=True, ensure_ascii=False))
            out.write("\n")

        print(f"Wrote {dest}")

def run_loop(mixer):
    while True:
        print("Commands")
        for k, v in cmds.items():
            print("%5s - %s %s" % (k, v["help"], f"(args: {v['args']})" if v["args"] else ""))

        try:
            command = input("command> ").split(" ")
        except EOFError:
            break

        if command[0].lower() not in cmds:
            print("Invalid command!")
        else:
            cmd = command[0].lower()
            args = command[1:]
            if cmd == "q":
                break
            try:
                func = getattr(mixer, cmds[cmd]["func"])
            except AttributeError:
                print(
                    f"Uh oh! Couldn't find the function '{cmds[cmd]['func']}'")
            nargs = len(cmds[cmd]["args"])
            if nargs != len(args):
                print(f"Expected {nargs} args, got {len(args)}")
            else:
                func(*args)
            print("")


if __name__ == "__main__":
    parser = ArgumentParser(description="Soundcraft Ui24r Mixer Utility")
    parser.add_argument(dest="config",
                        help="Input mixer configuration JSON")
    args = parser.parse_args()

    with open(args.config, "r") as config:
        mixer = Mixer(config.read())

    mixer.print_inputs()
    run_loop(mixer)
