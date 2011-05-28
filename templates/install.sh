#!/bin/bash

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec >/var/log/install.log
exec 2>&1 

rm -f /etc/cron.d/firstboot

# try to make screen usable - since install.sh is kicked off by cron, TERM is unset
export TERM="xterm

echo Setting root password
echo root:{password} | chpasswd

echo Injecting key
mkdir /root/.ssh
chmod 700 /root/.ssh
echo {pubkey} > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

echo Installing dependancies
apt-get install -y curl

echo Downloading and running auto.sh
cd /opt/
bash -c "curl -skS https://github.com/cloudbuilders/deploy.sh/raw/master/auto.sh | /bin/bash"

echo FINISHED
