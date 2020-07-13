#! /bin/sh

umask 0077

ansible_dir="/nixos_deploy"
keyfile="/root/.id_ec"
hostfile="${ansible_dir}/hosts.yml"
connection_timeout=120

echo "${NIXOS_ROBOT_KEY}" > "${keyfile}"
chmod 0400 "${keyfile}"

python3 "${ansible_dir}"/build_inventory.py \
  --keyfile "${keyfile}" \
  --timeout "${connection_timeout}" \
  --eventlog "${GITHUB_EVENT_PATH}" \
  --fixedhosts "${NIXOS_DEPLOY_FIXED_HOSTS}" \
  --fixedtunnelports "${NIXOS_DEPLOY_FIXED_TUNNEL_PORTS}" \
  > "${hostfile}"

export ANSIBLE_PYTHON_INTERPRETER="auto_silent"
export ANSIBLE_HOST_KEY_CHECKING="False"
export ANSIBLE_SSH_RETRIES=5
ansible-playbook --timeout="${connection_timeout}" \
                 --key-file "${keyfile}" \
                 --inventory "${hostfile}" \
                 --extra-vars "nixos_deploy_service=${NIXOS_DEPLOY_SERVICE}" \
                 "${ansible_dir}"/deploy.yml

