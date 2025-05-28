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
    s4 = net.addSwitch('s4')
    s5 = net.addSwitch('s5')

    net.addLink(s1, s2)
    net.addLink(s4, s5)
    net.addLink(s3, s5)

    net.start()

    CLI(net)

    net.stop()

if __name__ == '__main__':
    start_network()
