RADIO EDIT
==========

One click deploying of an integrated openstack cloud on rackspace cloud files.

OpenStack is under active development with many different projects:

 * nova - compute
 * glance - image delievery
 * swift - object storage
 * keystone - identity / authentication
 * dash - dashbaord

As they are all changing rapidly, we need a way to deploy an integrated system.  With a single button push an automated install.


Goal
----

Provide a webpage that:

 * Lists all running the stack
 * Can spawn a new stacks with the click of the button:
  * Starts a cloud server
  * Pulls down and runs auto.sh a la http://cloudbuilders.github.com/deploy.sh/hacking-nova.html
 * shutdown instances older than 24 hours via cron
 * make /latest always point to the most recent deploy at least 5 minutes


Later
-----

 * ajaxterm integration (single click to access console via ssh)
 * /foo should redirect to a test instance named foo
 * log integration
 * option to deploy specific revisions of components
 * kill a single stack
 * display a checkbox next to stacks that "work"


Installation
------------

    apt-get install -y python-cherrypy
    apt-get install -y python-paramiko
    git clone https://github.com/jacobian/openstack.compute.git
    cd openstack.compute
    python setup.py install

