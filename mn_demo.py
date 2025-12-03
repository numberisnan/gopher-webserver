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
    CONF_A = f'{PROJECT_DIR}/config_a.json'
    CONF_B = f'{PROJECT_DIR}/config_b.json'
    
    info('*** Starting Gopher server on h1 with config_a.json\n')
    h1.cmd(f'cd {PROJECT_DIR} && cp {CONF_A} config.json && python3 main.py >h1.log 2>&1 &')

    info('*** Starting Gopher server on h2 with config_b.json\n')
    h2.cmd(f'cd {PROJECT_DIR} && cp {CONF_B} config.json && python3 main.py >h2.log 2>&1 &')

    info('*** Give the servers a moment to start\n')
    h1.cmd('sleep 1')
    h2.cmd('sleep 1')

    info('\n*** Network is ready.\n')
    info('*** From the Mininet CLI, try:\n')
    info('    h1 tail -n +1 h1.log\n')
    info('    h2 tail -n +1 h2.log\n')
    info('    h2 openssl s_client -connect 10.0.0.1:<port-from-config-a> -crlf\n')
    info('    h1 openssl s_client -connect 10.0.0.2:<port-from-config-b> -crlf\n\n')

    CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
