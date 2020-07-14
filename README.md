# NixOS-deploy
Automatically run a deployment service on the configured servers.
Additional servers can be included by putting a directive in the commit message.

This action can be activated for a repository by adding a file containing
the following definition to `.github/workflows` in the concerned repository:
```
name: NixOS deploy

on:
  push:
    branches:
      - master
    paths-ignore:
      - <patterns to ignore>

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: msf-ocb/nixos-deploy@master
      env:
        NIXOS_ROBOT_KEY: ${{ secrets.NIXOS_ROBOT_KEY }}
        NIXOS_DEPLOY_SERVICE: '<service name>.service'
```

## Configuration

The following environment variables can be specified
in the workflow definition to configure the action:
1. `NIXOS_ROBOT_KEY` (required):
   the SSH private key for the `robot` user (cf. Keeper) used to connect to the remote servers.
   It is advisable to store this value as a github secret and to reference it like in the example above.
   Github secrets can either be defined at the organisation level and shared with
   selected repositories, or they can be defined on a per-repository basis.
1. `NIXOS_DEPLOY_SERVICE` (required):
   set the service to start to trigger the deployment
1. `NIXOS_DEPLOY_FIXED_HOSTS` (optional):
   list of host names to include by default on every run, separated by spaces
1. `NIXOS_DEPLOY_FIXED_TUNNEL_PORTS` (optional):
   list of tunnel ports for hosts to include by default on every run, separated by spaces

The action will run on the hosts defined using the two environment variables above.
Additionally, the action will pick up directives of the form `(x-nixos-rebuild:relay_port:XXXX)`
from the commit message and include the host at port `XXXX` on the relays.

