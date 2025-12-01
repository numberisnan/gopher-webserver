#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def run():
    net = Mininet(
        controller=None,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )

    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')

    info('*** Adding switch\n')
    s1 = net.addSwitch('s1', failMode='standalone')

    info('*** Creating links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)

    info('*** Starting network\n')
    net.start()

    # Change this
    PROJECT_DIR = '/mnt/c/Users/nadav/gopher-webserver'

    info('*** Starting Gopher server on h1\n')
    h1.cmd(f'cd {PROJECT_DIR} && python3 main.py >server.log 2>&1 &')

    info('*** Give the server a moment to start\n')
    h1.cmd('sleep 1')

    info('\n*** Network is ready.\n')
    info('*** From the Mininet CLI, run:\n')
    info('    h2 openssl s_client -connect 10.0.0.1:7070 -crlf\n')
    info('    (then type / and press Enter to get the Gopher menu)\n\n')

    CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
