#!/usr/bin/env python

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
import ConfigParser
from ConfigParser import SafeConfigParser


def get_base():
    return os.path.dirname(os.path.abspath(__file__))


def cycle(list):
    i = -1
    while True:
        try:
            i = i + 1
            yield list[i]
        except IndexError:
            i = 0
            yield list[i]


class RadioEdit(object):
    """Define methods necessary to make our web page work with cherrypy"""

    # using cron since injected files aren't executable
    base = get_base()
    chars = string.letters + string.digits

    def gen_password(self, length=8):
        pw = ""
        for i in range(length):
            pw += random.choice(self.chars)
        return pw

    def __init__(self, username,
                 apikey, pubkey,
                 prefix="nova",
                 auth_url="https://auth.api.rackspacecloud.com/v1.0",
                 private_key=None,
                 server_size=512):
        from openstack.compute import Compute
        self.prefix = prefix
        self.pubkey = pubkey
        self.first = ""
        self.compute = Compute(username=username,
                               apikey=apikey,
                               auth_url=auth_url)
        self.server_size = server_size
        self.private_key = private_key

    @cherrypy.expose
    def index(self):
        msg = ''
        style = cycle(["odd", "even"])
        try:
            servers = self.list()
            for server in servers:
                server['style'] = style.next()
        except Exception as e:
            msg = "Error: " + str(e)
            servers = []
        tmpl = open(self.base + '/templates/index.html').read()
        return jsontemplate.expand(tmpl, {'servers': servers, 'msg': msg})

    @cherrypy.expose
    def log(self, host, size=25, fn="/var/log/install.log"):
        try:
            import paramiko
            privatekeyfile = self.private_key
            mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username='root', pkey=mykey, timeout=2)
            stdin, stdout, stderr = \
                ssh.exec_command('tail -n %d "%s"' % (int(size), fn))
            log = stdout.read()
            ssh.close()
        except Exception, e:
            log = "Exception: %s" % e
        tmpl = open(self.base + '/templates/log.html').read()
        return jsontemplate.expand(tmpl, {'log': log, 'host': host})

    @cherrypy.expose
    def new(self, name=None):
        password = self.gen_password()
        img = [i for i in self.compute.images.list()
                if i.name.find("Ubuntu 10.10") != -1][0]
        flav = [f for f in self.compute.flavors.list() \
                    if f.ram == int(self.server_size)][0]
        srvname = self.prefix + str(uuid4()).replace('-', '')
        if name is None:
            name = self.prefix + '-' + str(uuid4()).replace('-', '')
        cron = "* * * * * root /bin/bash /root/install.sh\n"
        install = open(self.base + '/templates/install.sh').read().format(
            password=password, pubkey=self.pubkey)
        self.compute.servers.create(srvname, img.id, flav.id,
            files={"/etc/cron.d/firstboot": cron,
                   "/root/install.sh": install},
            meta={"created": \
                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
        servers = self.compute.servers.list()

        def info(s):
            return {'ip': s.public_ip,
                     'id': s.name,
                     'age': ago(s.metadata.get('created', None)),
                     'password': s.metadata.get('password', '?'),
                     'name': s.metadata.get('name', '?')}

        stack_servers = \
            [info(s) for s in servers if s.name.find(self.prefix) == 0]
        return sorted(stack_servers, key=lambda s: float(s['age']))


def ago(date_string, date_format="%Y-%m-%d %H:%M:%S"):
    try:
        d = datetime.datetime.strptime(date_string, date_format)
        n = datetime.datetime.now()
        diff = n - d
        return "%0.2f" % ((diff.days * 24) + (diff.seconds / 3600.0))
    except:
        return '0'


def setup_radio_edit(cfg=None):
    etc_cfg = "/etc/radioedit.cfg"
    cwd_path_cfg = os.path.join(
        get_base(),
        "radioedit.cfg")

    if not cfg and os.path.exists(etc_cfg):
        cfg = etc_cfg
    elif not cfg and os.path.exists(cwd_path_cfg):
        cfg = cwd_path_cfg
    else:
        raise Exception("No config file.")

    cp = SafeConfigParser()
    cp.read([cfg])
    username = cp.get("rackspacecloud", "user")
    apikey = cp.get("rackspacecloud", "apikey")
    prefix = cp.get("radioedit", "prefix")
    pubkey = cp.get("radioedit", "pubkey")
    try:
        server_size = cp.get("rackspacecloud", "server_size")
    except KeyError:
        server_size = 512
    except ConfigParser.NoOptionError:
        server_size = 512

    config_slash = {}
    try:
        if cp.get("radioedit", "password_protected").lower() in \
                ('no', 'false', 'off', '0'):
            password_protected = False
    except(KeyError, ConfigParser.NoOptionError):
        password_protected = True
    if password_protected:
        re_admin = cp.get("radioedit", "admin")
        re_admin_pass = cp.get("radioedit", "adminpass")
        users = {re_admin: re_admin_pass}
        config_slash = {'tools.basic_auth.on': True,
                        'tools.basic_auth.realm': 'Radioedit',
                        'tools.basic_auth.users': users,
                        'tools.basic_auth.encrypt': lambda x: x}

    try:
        auth_url = cp.get("rackspacecloud", "auth_url")
    except(KeyError, ConfigParser.NoOptionError):
        auth_url = "https://auth.api.rackspacecloud.com/v1.0"

    try:
        private_key = cp.get("radioedit", "privatekey")
    except(KeyError, ConfigParser.NoOptionError):
        private_key = os.path.expanduser('~/.ssh/id_rsa')

    conf = {'/': config_slash,
            '/static':
                 {'tools.staticdir.on': True,
                  'tools.staticdir.root': get_base(),
                  'tools.staticdir.dir': "static"},
           }
    return cherrypy.Application(
               RadioEdit(username,
                         apikey,
                         pubkey,
                         prefix=prefix,
                         auth_url=auth_url,
                         server_size=server_size,
                         private_key=private_key,
                         ),
               script_name=None, config=conf)

application = setup_radio_edit()

if __name__ == '__main__':
    cherrypy.quickstart(application.root, '/', application.config)
