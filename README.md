# NixOS-deploy
Automatically deploy the NixOS configuration

This action can be included by adding a file containing the following definition to `.github/workflows`:
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
        VAULT_PASS: ${{ secrets.VAULT_PASS }} # variable containing the passphrase for the Ansible vault
        NIXOS_DEPLOY_FIXED_HOSTS: '<space-separated list of hosts>' # list of hosts to update on every run
```

The action will pick up directives of the form `(x-nixos-rebuild:relay_port:XXXX)` and include the host at port `XXXX` on the relays.
