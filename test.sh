#! /usr/bin/env nix-shell
#! nix-shell -i bash

output="$(nix develop '.#default' --command ./build_inventory.py \
            --sshrelay_domain sshrelay.ocb.msf.org \
            --sshrelay_user tunneller \
            --sshrelay_port 443 \
            --eventlog ./test/github_event_log.json \
            --fixedhosts 'sshrelay2.ocb.msf.org sshrelay1.ocb.msf.org' \
            --fixedtunnelports "1 2 3" \
            --keyfile /dev/null \
            --timeout 90)"

diff --report-identical-files --side-by-side <(echo "${output}") ./golden_file.yml
