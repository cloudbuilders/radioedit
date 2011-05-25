#!/usr/bin/python

# Copyright (c) 2011 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
#} limitations under the License.


import json
import openstack.compute
import datetime
import cherrypy
import datetime
import json
from mako.template import Template
from mako.lookup import TemplateLookup
import openstack.compute
import os
import random
import string
from uuid import uuid4
from ConfigParser import SafeConfigParser
import os
import random
import string

class RadioEdit(object):
    """Define methods necessary to make our web page work with cherrypy"""

    # using cron since injected files aren't executable

    crond = "* * * * * root /bin/bash /root/install.sh\n"
    chars = string.letters + string.digits
    def gen_password(self, length=8):
        pw = ""
        for i in range(length):
            pw += self.chars[random.randint(0,len(self.chars))]
        return pw
                    
    def __init__(self, cfg="cloud.cfg"):
        from openstack.compute import Compute
        cp = SafeConfigParser()
        cp.read([cfg])
        username = cp.get("rackspacecloud", "user")
        apikey = cp.get("rackspacecloud", "apikey")
        self.first = ""
        self.prefix = cp.get("radioedit", "prefix")
        self.pubkey = cp.get("radioedit", "pubkey")
        self.compute = Compute(username=username, apikey=apikey)
        self.root_install = """#!/bin/bash

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec >/tmp/install.log
exec 2>&1 

echo root:%s | chpasswd

echo STARTING
mkdir /root/.ssh
chmod 700 /root/.ssh
echo %s > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
rm -f /etc/cron.d/firstboot
touch /tmp/foo
apt-get install -y curl screen
cd /opt/
bash -c "curl -skS https://github.com/cloudbuilders/deploy.sh/raw/master/auto.sh | /bin/bash"
echo FINISHED
"""

    @cherrypy.expose
    def index(self):
        try:
            servers = self.list()
        except:
            servers = []
        return '<html><head><title>[radioedit]</title></head><body><form method="get" action="/new"><input type="text" name="name" /></form><br/><form method="post" action="/reset"><input type="submit" value="kill all" /></form><br /><table>' + reduce(
               lambda x,y: x+y,
               map(lambda x: '<tr><td><a href="http://%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>' % 
               (x['ip'], x['name'], x['ip'], x['password'], x['created']), servers), "") + "</table></body></html>"
            
    @cherrypy.expose
    def new(self, name=None):
        passwd = self.gen_password()
        img = [i for i in self.compute.images.list()
                if i.name.find("Ubuntu 10.10") != -1][0]
        flav = [f for f in self.compute.flavors.list() if f.ram == 512][0]
        srvname = self.prefix + str(uuid4()).replace('-', '')
        if name is None:
            name = self.prefix + str(uuid4()).replace('-', '')
        self.compute.servers.create(srvname, img.id, flav.id,
            files={"/etc/cron.d/firstboot": self.crond,
                   "/root/install.sh": self.root_install % (passwd, self.pubkey)},
            meta={"created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  "name": name,
                  "password": password})
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def reset(self):
        servers = self.compute.servers.list()
        for server in servers:
            if server.name.find(self.prefix) == 0:
                self.compute.servers.delete(server)
        raise cherrypy.HTTPRedirect("/")

    def list(self):
        return [{"ip": s.public_ip, 
                "created": s.metadata.has_key('created') and s.metadata['created'] or "Unknown",
                "password": s.metadata.has_key('password') and s.metadata['password'] or "Unknown",
                "name": s.metadata.has_key('name') and s.metadata['name'] or s.name}
                  for s in self.compute.servers.list()
                  if s.name.find(self.prefix) == 0]

application = cherrypy.Application(RadioEdit(cfg="/etc/cloud.cfg"), script_name=None, config=None)
