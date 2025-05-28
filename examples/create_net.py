from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

def start_network():
    net = Mininet()

    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    h1 = net.addHost('h1') # Hosts won't be fetched by RYU Northbound API even if linked to a switch

    net.addLink(s1, s2)
    net.addLink(s2, s3)

    net.start()

    CLI(net)

    net.stop()

if __name__ == '__main__':
    start_network()
