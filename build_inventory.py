#! /usr/bin/env python3

import argparse
import itertools
import json
import re

# Regex to match the directive
#   (x-nixos:rebuild:relay_port:XXXX)
# in commit messages, signaling to include the host at port XXXX at the relays
commit_directive_regex = re.compile(
  r'\(x-nixos:rebuild:relay_port:([1-9][0-9]*)\)'
)

def configure_yaml(yaml):
  yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
  )

def args_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('--fixedhosts',       type=str, dest='fixed_hosts', required=False, default="")
  parser.add_argument('--fixedtunnelports', type=str, dest='fixed_ports', required=False, default="")
  parser.add_argument('--eventlog',         type=str, dest='event_log',   required=True)
  parser.add_argument('--keyfile',          type=str, dest='key_file',    required=True)
  parser.add_argument('--timeout',          type=int, dest='time_out',    required=True)
  parser.add_argument('--json', dest='use_json', action='store_true',     required=False)
  return parser

def get_ports(commit_message):
  ms = commit_directive_regex.finditer(commit_message)
  # Group 0 is the full matched expression, group 1 is the first subgroup
  return map(lambda m: m.group(1), ms)

def ports(event_log):
  with open(event_log, 'r') as f:
    data = json.load(f)
  return { port
           for commit in data["commits"]
           for port in get_ports(commit["message"]) }

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
                                                             "-o StrictHostKeyChecking=yes " + \
                                                             "-l tunneller " + \
                                                             "sshrelay.ocb.msf.org'"
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
    return json.dumps(inv, indent=2)
  else:
    import yaml
    configure_yaml(yaml)
    return yaml.safe_dump(inv, indent=2,
                               default_flow_style=False,
                               width=120)

def go():
  args = args_parser().parse_args()
  tunnel_ports = itertools.chain(args.fixed_ports.split(),
                                 ports(args.event_log))
  print(write_inventory(inventory(args.fixed_hosts.split(),
                                  tunnel_ports,
                                  args.key_file,
                                  args.time_out),
                        args.use_json))

if __name__ == "__main__":
  go()

