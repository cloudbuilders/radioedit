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
from operator import itemgetter

class RadioEdit(object):
    """Define methods necessary to make our web page work with cherrypy"""

    # using cron since injected files aren't executable
    base = os.path.dirname(os.path.abspath(__file__))
    chars = string.letters + string.digits

    def gen_password(self, length=8):
        pw = ""
        for i in range(length):
            pw += random.choice(self.chars)
        return pw
                    
    def __init__(self, username, apikey, pubkey, prefix="nova"):
        from openstack.compute import Compute
        self.prefix = prefix
        self.pubkey = pubkey
        self.first = ""
        self.compute = Compute(username=username, apikey=apikey)

    @cherrypy.expose
    def index(self):
        exception = None
        try:
            servers = self.list()
        except Exception, e:
            exception = True
            msg  = e.msg
            servers = []
        tmpl = open(self.base+'/templates/index.html').read()
        return jsontemplate.expand(tmpl, {'servers': servers, 'exception': exception, msg: msg})

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
        return sorted([{"ip": s.public_ip, 'id': s.name,
            "created": ago(s.metadata.has_key('created') and s.metadata['created'] or "Unknown", "%Y-%m-%d %H:%M:%S"),
            "date_created": (s.metadata.has_key('created') and 
                s.metadata['created'] or "1970-01-01 00:00:00"),
            "password": s.metadata.has_key('password') and s.metadata['password'] or "Unknown",
            "name": s.metadata.has_key('name') and s.metadata['name'] or s.name}
            for s in self.compute.servers.list()
            if s.name.find(self.prefix) == 0], key=lambda x:
                datetime.datetime.strptime(x['date_created'],
                "%Y-%m-%d %H:%M:%S"))

def ago(date_string, date_format):
    if date_string == "Unknown": return date_string
    d = datetime.datetime.strptime(date_string, date_format)
    n = datetime.datetime.now()
    diff = n - d
    return "%0.2f hours ago" % (diff.total_seconds() / 3600)

def setup_radio_edit(cfg="/etc/radioedit.cfg"):
    cp = SafeConfigParser()
    cp.read([cfg])
    username = cp.get("rackspacecloud", "user")
    apikey = cp.get("rackspacecloud", "apikey")
    prefix = cp.get("radioedit", "prefix")
    pubkey = cp.get("radioedit", "pubkey")
    re_admin = cp.get("radioedit", "admin")
    re_admin_pass = cp.get("radioedit", "adminpass")
    users = { re_admin: re_admin_pass }
    conf = {'/': 
                 {'tools.basic_auth.on': True,
                  'tools.basic_auth.realm': 'Radioedit',
                  'tools.basic_auth.users': users,
                  'tools.basic_auth.encrypt': lambda x: x}}
    return cherrypy.Application(
               RadioEdit(username,apikey,pubkey,prefix),
               script_name=None, config=conf)

application = setup_radio_edit()

if __name__ == '__main__':
    cherrypy.quickstart(application.root, '/', application.config)
