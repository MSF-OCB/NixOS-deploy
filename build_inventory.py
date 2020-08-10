#! /usr/bin/env python3

import argparse
import itertools
import json
import re

def configure_yaml(yaml):
  yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
  )

def args_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('--fixedhosts', type=str, required=False, dest='fixed_hosts', default="")
  parser.add_argument('--fixedtunnelports', type=str, required=False, dest='fixed_ports', default="")
  parser.add_argument('--eventlog', type=str, required=True,  dest='event_log')
  parser.add_argument('--keyfile',  type=str, required=True,  dest='key_file')
  parser.add_argument('--timeout',  type=int, required=True,  dest='time_out')
  parser.add_argument('--json', required=False, dest='use_json', action='store_true')
  return parser

def get_ports(regex, commit_message):
  ms = regex.finditer(commit_message)
  # Group 0 is the full matched expression, group 1 is the first subgroup
  return map(lambda m: m.group(1), ms)

def ports(event_log):
  with open(event_log, 'r') as f:
    data = json.load(f)
  regex = re.compile(r'\(x-nixos:rebuild:relay_port:([1-9][0-9]*)\)')
  return { port
           for commit in data["commits"]
           for port in get_ports(regex, commit["message"]) }

def inventory_definition(tunnel_ports):
  return { f"tunnelled_{port}": { "ansible_port": port } for port in tunnel_ports }

def inventory(fixed_hosts, tunnel_ports, key_file, time_out):
  return {
    "all": {
      "children": {
        "direct_hosts": {
          "hosts": { key: None for key in fixed_hosts }
        },
        "tunnelled": {
          "hosts": inventory_definition(tunnel_ports),
          "vars": {
            "ansible_host": "localhost",
            "ansible_ssh_common_args": f"-o 'ProxyCommand=ssh -W %h:%p " + \
                                                            f"-i {key_file} " + \
                                                             "-p 22 " + \
                                                            f"-o ConnectTimeout={time_out} " + \
                                                             "-o StrictHostKeyChecking=no " + \
                                                             "tunneller@sshrelay2.msf.be'"
          }
        }
      },
      "vars": {
        "ansible_user": "robot"
      }
    }
  }

def write_inventory(inv, use_json):
  if use_json:
    print(json.dumps(inv, indent=2))
  else:
    import yaml
    configure_yaml(yaml)
    print(yaml.safe_dump(inv, indent=2,
                              default_flow_style=False,
                              width=120))

def go():
  args = args_parser().parse_args()
  tunnel_ports = itertools.chain(args.fixed_ports.split(),
                                 ports(args.event_log))
  write_inventory(inventory(args.fixed_hosts.split(),
                            tunnel_ports,
                            args.key_file,
                            args.time_out),
                  args.use_json)

if __name__ == "__main__":
  go()

