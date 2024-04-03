#! /usr/bin/env bash

set -e

robot_key="${INPUT_NIXOS_ROBOT_KEY}"
deploy_service="${INPUT_NIXOS_DEPLOY_SERVICE}"
fixedhosts="${INPUT_NIXOS_DEPLOY_FIXED_HOSTS}"
fixedports="${INPUT_NIXOS_DEPLOY_FIXED_TUNNEL_PORTS}"
sshrelay_domain="${INPUT_NIXOS_DEPLOY_SSHRELAY_DOMAIN}"
sshrelay_user="${INPUT_NIXOS_DEPLOY_SSHRELAY_USER}"
sshrelay_port="${INPUT_NIXOS_DEPLOY_SSHRELAY_PORT}"
sshrelay_pubkey="${INPUT_NIXOS_DEPLOY_SSHRELAY_PUBLIC_KEY}"

umask 0077

action_dir="${GITHUB_ACTION_PATH}"
keyfile="${action_dir}/id_robot"
hostfile="${action_dir}/hosts.yml"
connection_timeout=120

echo "${robot_key}" > "${keyfile}"
chmod 0400 "${keyfile}"

mkdir --parent ~/.ssh
cat <<EOF > ~/.ssh/known_hosts
${sshrelay_domain} ${sshrelay_pubkey}
EOF

python3 "${action_dir}"/build_inventory.py \
  --keyfile "${keyfile}" \
  --timeout "${connection_timeout}" \
  --eventlog "${GITHUB_EVENT_PATH}" \
  --fixedhosts "${fixedhosts}" \
  --fixedtunnelports "${fixedports}" \
  --sshrelay_domain "${sshrelay_domain}" \
  --sshrelay_user "${sshrelay_user}" \
  --sshrelay_port "${sshrelay_port}" \
  > "${hostfile}"

echo "Calling the Ansible playbook with the following inventory:"
cat "${hostfile}"

export ANSIBLE_PYTHON_INTERPRETER="auto_silent"
export ANSIBLE_HOST_KEY_CHECKING="False"
export ANSIBLE_SSH_RETRIES=5
ansible-playbook --forks 100 \
                 --timeout="${connection_timeout}" \
                 --key-file "${keyfile}" \
                 --inventory "${hostfile}" \
                 --extra-vars "nixos_deploy_service=${deploy_service}" \
                 "${action_dir}"/deploy.yml
