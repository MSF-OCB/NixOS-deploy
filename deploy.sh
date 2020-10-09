#! /bin/sh

robot_key="${INPUT_NIXOS_ROBOT_KEY}"
deploy_service="${INPUT_NIXOS_DEPLOY_SERVICE}"
fixedhosts="${INPUT_NIXOS_DEPLOY_FIXED_HOSTS}"
fixedports="${INPUT_NIXOS_DEPLOY_FIXED_TUNNEL_PORTS}"

umask 0077

ansible_dir="/nixos_deploy"
keyfile="/root/.id_ec"
hostfile="${ansible_dir}/hosts.yml"
connection_timeout=120

echo "${robot_key}" > "${keyfile}"
chmod 0400 "${keyfile}"

cat <<EOF > /etc/ssh/ssh_known_hosts
sshrelay.ocb.msf.org ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDsn2Dvtzm6jJyL9SJY6D1/lRwhFeWR5bQtSSQv6bZYf
EOF

python3 "${ansible_dir}"/build_inventory.py \
  --keyfile "${keyfile}" \
  --timeout "${connection_timeout}" \
  --eventlog "${GITHUB_EVENT_PATH}" \
  --fixedhosts "${fixedhosts}" \
  --fixedtunnelports "${fixedports}" \
  > "${hostfile}"

echo "Calling the Ansible playbook with the following inventory:"
cat "${hostfile}"

export ANSIBLE_PYTHON_INTERPRETER="auto_silent"
export ANSIBLE_HOST_KEY_CHECKING="False"
export ANSIBLE_SSH_RETRIES=5
ansible-playbook --timeout="${connection_timeout}" \
                 --key-file "${keyfile}" \
                 --inventory "${hostfile}" \
                 --extra-vars "nixos_deploy_service=${deploy_service}" \
                 "${ansible_dir}"/deploy.yml

