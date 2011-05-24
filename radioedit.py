#!/usr/bin/python

import json
import openstack.compute
from uuid import uuid4
from ConfigParser import SafeConfigParser


class Root(object):
    """Define methods necessary to make our web page work with cherrypy"""

    def __init__(self, cfg="cloud.cfg"):
        from openstack.compute import Compute
        cp = SafeConfigParser()
        cp.read([cfg])
        self.user = cp.get("rackspacecloud", "user")
        self.apikey = cp.get("rackspacecloud", "apikey")
        self.compute = Compute(username=self.user, apikey=self.apikey)
        self.prefix = cp.get("radioedit", "prefix")

    def new_instance(self):
        img = [x for x in self.compute.images.list()
                if x.name.find("Ubuntu 10.10") != -1][0]
        flav = [x for x in self.compute.flavors.list() if x.ram == 512][0]
        name = self.prefix + str(uuid4())
        return self.compute.servers.create(name, img.id, flav.id)

    def reset(self):
        for server in self.compute.servers.list():
            if server.name.find(self.prefix) == 0:
                self.compute.servers.delete(server)

    def list_instances(self):
        return


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-c", "--configfile", dest="config_file",
                      default="cloud.cfg")
    (options, args) = parser.parse_args()

    root = Root(options.config_file)
    print root.user, root.apikey, root.compute
    print root.compute.servers.list()
