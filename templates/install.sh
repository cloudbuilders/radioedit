#!/bin/bash
SRVTYPE={srvtype}
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec >/var/log/install.log
exec 2>&1 

rm -f /etc/cron.d/firstboot

# try to make screen usable - since install.sh is kicked off by cron, TERM is unset
export TERM="xterm"

echo Setting root password
echo root:{password} | chpasswd

echo Injecting key
mkdir /root/.ssh
chmod 700 /root/.ssh
echo {pubkey} > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

echo Installing dependancies
apt-get install -y curl


if [[ "$SRVTYPE" == "swift" ]];then
    echo "Installing swift"
    bash -c "curl -skS https://raw.github.com/cloudbuilders/deploy.sh/master/swift.sh | /bin/bash"
else
    echo Downloading and running auto.sh
    cd /opt/

    #By default installing nova
    echo "Installing nova"
    bash -c "curl -skS https://raw.github.com/cloudbuilders/deploy.sh/master/auto.sh | env CLOUDSERVER=1 NOVASCRIPTURL={novascript_url} /bin/bash"
fi

echo FINISHED
