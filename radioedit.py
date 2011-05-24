#!/usr/bin/python

import json
import openstack.compute
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
