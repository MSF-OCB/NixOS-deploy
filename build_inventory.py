#! /usr/bin/env python3

import argparse
import itertools
import json
import re

from typing import Iterable, Mapping, Set


# Regex to match the directive
#   (x-nixos:rebuild:relay_port:XXXX)
# in commit messages, signaling to include the host at port XXXX at the relays
commit_directive_regex = re.compile(r"\(x-nixos:rebuild:relay_port:([1-9][0-9]{,4})\)")


def configure_yaml(yaml):
    yaml.SafeDumper.add_representer(
        type(None),
        lambda dumper, _: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
    )


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sshrelay_domain", type=str, dest="sshrelay_domain", required=True
    )
    parser.add_argument(
        "--sshrelay_user", type=str, dest="sshrelay_user", required=True
    )
    parser.add_argument(
        "--sshrelay_port", type=int, dest="sshrelay_port", required=True
    )
    parser.add_argument(
        "--fixedhosts", type=str, dest="fixed_hosts", required=False, default=""
    )
    parser.add_argument(
        "--fixedtunnelports", type=str, dest="fixed_ports", required=False, default=""
    )
    parser.add_argument("--eventlog", type=str, dest="event_log", required=True)
    parser.add_argument("--keyfile", type=str, dest="key_file", required=True)
    parser.add_argument("--timeout", type=int, dest="time_out", required=True)
    parser.add_argument("--json", dest="use_json", action="store_true", required=False)
    return parser


def is_port(port: str) -> bool:
    return port.isdigit() and (int(port) < 2**16)


def toInt(s: str) -> int:
    return int(s)


def get_ports(commit_message: str) -> Iterable[int]:
    ms = commit_directive_regex.finditer(commit_message)
    # Group 0 is the full matched expression, group 1 is the first subgroup
    return map(toInt, filter(is_port, map(lambda m: m.group(1), ms)))


def ports(event_log: str) -> Iterable[int]:
    with open(event_log, "r") as f:
        data = json.load(f)
    return {
        port
        for commit in data.get("commits", [])
        for port in get_ports(commit["message"])
    }


def inventory_definition(tunnel_ports: Iterable[int]):
    return {f"tunnelled_{port}": {"ansible_port": port} for port in tunnel_ports}


def inventory(
    fixed_hosts: Set[str],
    sshrelay_domain: str,
    sshrelay_user: str,
    sshrelay_port: int,
    tunnel_ports: Set[int],
    key_file: str,
    time_out: int,
) -> Mapping:
    return {
        "all": {
            "children": {
                "direct_hosts": {
                    "hosts": {fixed_host: None for fixed_host in fixed_hosts}
                },
                "tunnelled": {
                    "hosts": inventory_definition(tunnel_ports),
                    "vars": {
                        "ansible_host": "localhost",
                        "ansible_ssh_common_args": "-o 'ProxyCommand=ssh -W %h:%p "
                        + f"-i {key_file} "
                        + f"-p {sshrelay_port} "
                        + f"-o ConnectTimeout={time_out} "
                        + "-o StrictHostKeyChecking=yes "
                        + f"-l {sshrelay_user} "
                        + f"{sshrelay_domain}'",
                    },
                },
            },
            "vars": {"ansible_user": "robot"},
        }
    }


def write_inventory(inv: Mapping, use_json: bool) -> str:
    if use_json:
        return json.dumps(inv, indent=2)
    else:
        import yaml

        configure_yaml(yaml)
        return yaml.safe_dump(inv, indent=2, default_flow_style=False, width=120)


def main() -> None:
    args = args_parser().parse_args()
    tunnel_ports = set(
        itertools.chain(map(toInt, args.fixed_ports.split()), ports(args.event_log))
    )
    print(
        write_inventory(
            inventory(
                set(args.fixed_hosts.split()),
                args.sshrelay_domain,
                args.sshrelay_user,
                args.sshrelay_port,
                tunnel_ports,
                args.key_file,
                args.time_out,
            ),
            args.use_json,
        )
    )


if __name__ == "__main__":
    main()
