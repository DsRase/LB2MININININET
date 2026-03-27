from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
import time
import ruleManager


class SecurityTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')

        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        h3 = self.addHost('h3', ip='10.0.2.1/24')
        h4 = self.addHost('h4', ip='10.0.2.2/24')
        gw = self.addHost('gw')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        self.addLink(gw, s1)
        self.addLink(gw, s2)
        self.addLink(s1, s2)

def run_security_topology():
    topo = SecurityTopo()
    net = Mininet(topo=topo, controller=None)

    onos_controller = RemoteController('onos', ip='127.0.0.1', port=6653)
    net.addController(onos_controller)

    info("*** Starting network\n")
    net.start()

    info("*** Waiting for switches to connect...\n")
    time.sleep(5)

    # Настройка маршрутов
    info("*** Setting up routes\n")

    net['h1'].cmd('ip route add default via 10.0.1.254')
    net['h2'].cmd('ip route add default via 10.0.1.254')
    net['h3'].cmd('ip route add default via 10.0.2.254')
    net['h4'].cmd('ip route add default via 10.0.2.254')

    # У gw два интерфейса
    net['gw'].cmd('ip addr add 10.0.1.254/24 dev gw-eth0')
    net['gw'].cmd('ip addr add 10.0.2.254/24 dev gw-eth1')
    net['gw'].cmd('ip link set gw-eth0 up')
    net['gw'].cmd('ip link set gw-eth1 up')
    net['gw'].cmd('echo 1 > /proc/sys/net/ipv4/ip_forward')

    # Применяем flow rules
    info("\n*** Applying ONOS flow rules\n")
    success = ruleManager.apply_rules(net)

    if success:
        info("\n*** Flow rules applied successfully\n")
    else:
        info("\n*** Failed to apply flow rules\n")

    print("\n" + "=" * 10 + " Topology started " + "=" * 10)
    print("Working net: h1, h2")
    print("Guest net: h3, h4")
    print("Gateway: gw")
    print("\nTest commands:")
    print("  h1 ping h2    # Should work")
    print("  h1 ping gw  # Should work")
    print("  h1 ping h3    # Should FAIL (isolation)")
    print("  h3 ping h4    # Should work")
    print("  h3 ping gw  # Should work")
    print("  h3 ping h1    # Should FAIL (isolation)")

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run_security_topology()