from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSSwitch
import time

from ruleManager import apply_qos_rules


class QoSTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', protocols='OpenFlow13')
        s4 = self.addSwitch('s4', protocols='OpenFlow13')

        voip_source = self.addHost('h1', ip='10.0.1.1/24', mac='00:00:00:00:01:01')
        voip_dest = self.addHost('h2', ip='10.0.1.2/24', mac='00:00:00:00:01:02')
        normal_source = self.addHost('h3', ip='10.0.2.1/24', mac='00:00:00:00:02:01')
        normal_dest = self.addHost('h4', ip='10.0.2.2/24', mac='00:00:00:00:02:02')

        self.addLink(voip_source, s1)
        self.addLink(voip_dest, s3)
        self.addLink(normal_source, s1)
        self.addLink(normal_dest, s3)

        self.addLink(s1, s2, bw=100, delay='2ms', loss=0, use_htb=True)
        self.addLink(s2, s3, bw=100, delay='2ms', loss=0, use_htb=True)

        self.addLink(s1, s4, bw=10, delay='20ms', loss=1, use_htb=True)
        self.addLink(s4, s3, bw=10, delay='20ms', loss=1, use_htb=True)

def run_topology():
    topo = QoSTopo()
    net = Mininet(topo=topo, link=TCLink, controller=None, switch=OVSSwitch)

    onos = RemoteController('onos', ip='127.0.0.1', port=6653)
    net.addController(onos)
    net.start()

    time.sleep(2)
    for sw in ['s1', 's2', 's3', 's4']:
        net[sw].cmd(f'ovs-vsctl set bridge {sw} protocols=OpenFlow13')
        net[sw].cmd(f'ovs-vsctl set-controller {sw} tcp:127.0.0.1:6653')

    time.sleep(3)

    apply_qos_rules(net)

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run_topology()