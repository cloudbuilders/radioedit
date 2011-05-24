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
# limitations under the License.


import json
import openstack.compute
import datetime
import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
from uuid import uuid4
from ConfigParser import SafeConfigParser
import os


class Root(object):
    """Define methods necessary to make our web page work with cherrypy"""
    crond = "* * * * * root /bin/bash /root/install.sh\n"

    def __init__(self, cfg="cloud.cfg"):
        from openstack.compute import Compute
        cp = SafeConfigParser()
        cp.read([cfg])
        self.first = ""
        self.user = cp.get("rackspacecloud", "user")
        self.apikey = cp.get("rackspacecloud", "apikey")
        self.prefix = cp.get("radioedit", "prefix")
        self.pubkey = cp.get("radioedit", "pubkey")
        self.compute = Compute(username=self.user, apikey=self.apikey)
        self.root_install = """#!/bin/bash

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec >/tmp/install.log
exec 2>&1 

echo STARTING
mkdir /root/.ssh
chmod 700 /root/.ssh
echo %s > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
rm -f /etc/cron.d/firstboot
touch /tmp/foo
apt-get install -y curl
cd /opt/
curl -skS https://github.com/cloudbuilders/deploy.sh/raw/master/auto.sh | /bin/bash
echo FINISHED
""" % (self.pubkey) 

    @cherrypy.expose
    def index(self):
        return '<html><body><form method="get" action="/new"><input type="text" name="name" /></form><br/><form method="post" action="/reset"><input type="submit" value="kill all" /></form><br /><table>' + reduce(
               lambda x,y: x+y,
               map(lambda x: '<tr><td><a href="http://%s">%s</a></td><td>%s</td><td>%s</td></tr>' % 
               (x['ip'], x['name'].split('-')[1], x['ip'], x['name'].split('-')[2]), self.list()), "") + "</table></body></html>"

    @cherrypy.expose
    def new(self, name=None):
        img = [i for i in self.compute.images.list()
                if i.name.find("Ubuntu 10.10") != -1][0]
        flav = [f for f in self.compute.flavors.list() if f.ram == 512][0]
        if name is None:
            name = str(uuid4()).replace('-', '')
        full_name = self.prefix + '-' + name + '-' + str(datetime.datetime.today()).replace('-', ' ')
        srv = self.compute.servers.create(full_name.replace(' ','_'), img.id, flav.id,
            files={"/etc/cron.d/firstboot": self.crond,
                   "/root/install.sh": self.root_install})
        if self.first == "":
            self.first = srv.public_ip
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def reset(self):
        self.first = ""
        servers = self.compute.servers.list()
        for server in servers:
            if server.name.find(self.prefix) == 0:
                self.compute.servers.delete(server)
        raise cherrypy.HTTPRedirect("/")

    def list(self):
        return [{"ip": s.public_ip, "name": s.name}
                  for s in self.compute.servers.list()
                  if s.name.find(self.prefix) == 0]

application = cherrypy.Application(Root(cfg="/etc/cloud.cfg"), script_name=None, config=None)