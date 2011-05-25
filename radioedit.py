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


import openstack.compute
import datetime
import cherrypy
import jsontemplate
import os
import random
import string
from uuid import uuid4
from ConfigParser import SafeConfigParser

class RadioEdit(object):
    """Define methods necessary to make our web page work with cherrypy"""

    # using cron since injected files aren't executable

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
        self.base = os.path.dirname(os.path.abspath(__file__))

    @cherrypy.expose
    def index(self):
        try:
            servers = self.list()
        except:
            servers = []
        tmpl = open(self.base+'/templates/index.html').read()
        return jsontemplate.expand(tmpl, {'servers': servers})

    @cherrypy.expose
    def new(self, name=None):
        password = self.gen_password()
        img = [i for i in self.compute.images.list()
                if i.name.find("Ubuntu 10.10") != -1][0]
        flav = [f for f in self.compute.flavors.list() if f.ram == 512][0]
        srvname = self.prefix + str(uuid4()).replace('-', '')
        if name is None:
            name = self.prefix + '-' + str(uuid4()).replace('-', '')
        cron = "* * * * * root /bin/bash /root/install.sh\n"
        install = open(self.base+'/templates/install.sh').read().format(password=password, pubkey=self.pubkey)
        self.compute.servers.create(srvname, img.id, flav.id,
            files={"/etc/cron.d/firstboot": cron,
                   "/root/install.sh": install},
            meta={"created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  "name": name,
                  "password": password})
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def kill(self, name=None, all=None):
        servers = self.compute.servers.list()
        for server in servers:
            if server.name.find(self.prefix) == 0:
                if all or name == server.name:
                    self.compute.servers.delete(server)
        raise cherrypy.HTTPRedirect("/")

    def list(self):
        return [{"ip": s.public_ip, 'id': s.name,
                "created": s.metadata.has_key('created') and s.metadata['created'] or "Unknown",
                "password": s.metadata.has_key('password') and s.metadata['password'] or "Unknown",
                "name": s.metadata.has_key('name') and s.metadata['name'] or s.name}
                  for s in self.compute.servers.list()
                  if s.name.find(self.prefix) == 0]

application = cherrypy.Application(RadioEdit('/etc/radioedit.cfg'), script_name=None, config=None)

if __name__ == '__main__':
    cherrypy.quickstart(RadioEdit('/etc/radioedit.cfg'))
