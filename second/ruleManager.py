import requests
import json
import time
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()


class ONOSFlowManager:
    def __init__(self, user='karaf', password='karaf'):
        self.base_url = "http://localhost:8181/onos/v1"
        self.auth = HTTPBasicAuth(user, password)
        self.headers = {'Content-Type': 'application/json'}

    def get_devices(self):
        try:
            response = requests.get(
                f"{self.base_url}/devices",
                auth=self.auth,
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('devices', []), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def add_flow(self, device_id, flow_rule):
        try:
            response = requests.post(
                f"{self.base_url}/flows/{device_id}",
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(flow_rule),
                timeout=5
            )
            if response.status_code in [200, 201]:
                return True, None
            return False, f"{response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    def delete_all_flows(self, device_id):
        try:
            response = requests.delete(
                f"{self.base_url}/flows/{device_id}",
                auth=self.auth,
                timeout=5
            )
            return response.status_code == 204, None
        except:
            return False, "Error"

    def discover_ports(self, net):
        ports = {}
        for sw in ['s1', 's2', 's3', 's4']:
            sw_ports = {}
            for name, intf in net[sw].nameToIntf.items():
                if name == 'lo':
                    continue
                port_num = net[sw].ports[intf]
                link = intf.link
                if link:
                    if link.intf1.node.name == sw:
                        other = link.intf2.node.name
                    else:
                        other = link.intf1.node.name
                    sw_ports[other] = port_num
                else:
                    sw_ports[name] = port_num
            ports[sw] = sw_ports
        return ports

    def apply_qos_rules(self, net):
        ports = self.discover_ports(net)

        s1_id = 'of:0000000000000001'
        s2_id = 'of:0000000000000002'
        s3_id = 'of:0000000000000003'
        s4_id = 'of:0000000000000004'

        s1_ports = ports['s1']
        s2_ports = ports['s2']
        s3_ports = ports['s3']

        for dev_id in [s1_id, s2_id, s3_id, s4_id]:
            self.delete_all_flows(dev_id)

        time.sleep(1)

        for dev_id in [s1_id, s2_id, s3_id, s4_id]:
            rule = {
                "priority": 50000,
                "isPermanent": True,
                "deviceId": dev_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": "FLOOD"}]},
                "selector": {"criteria": [{"type": "ETH_TYPE", "ethType": "0x0806"}]}
            }
            success, _ = self.add_flow(dev_id, rule)

        if 's2' in s1_ports:
            rule = {
                "priority": 40000,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": str(s1_ports['s2'])}]},
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.1/32"},
                        {"type": "IPV4_DST", "ip": "10.0.1.2/32"}
                    ]
                }
            }
            success, err = self.add_flow(s1_id, rule)

        if 's3' in s2_ports:
            rule = {
                "priority": 40000,
                "isPermanent": True,
                "deviceId": s2_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": str(s2_ports['s3'])}]},
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.1/32"},
                        {"type": "IPV4_DST", "ip": "10.0.1.2/32"}
                    ]
                }
            }
            success, err = self.add_flow(s2_id, rule)

        # S3: -> на h2
        if 'h2' in s3_ports:
            rule = {
                "priority": 40000,
                "isPermanent": True,
                "deviceId": s3_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": str(s3_ports['h2'])}]},
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_DST", "ip": "10.0.1.2/32"}
                    ]
                }
            }
            success, err = self.add_flow(s3_id, rule)

        if 's2' in s3_ports:
            rule = {
                "priority": 40000,
                "isPermanent": True,
                "deviceId": s3_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": str(s3_ports['s2'])}]},
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.2/32"},
                        {"type": "IPV4_DST", "ip": "10.0.1.1/32"}
                    ]
                }
            }
            success, err = self.add_flow(s3_id, rule)

        if 's1' in s2_ports:
            rule = {
                "priority": 40000,
                "isPermanent": True,
                "deviceId": s2_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": str(s2_ports['s1'])}]},
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.2/32"},
                        {"type": "IPV4_DST", "ip": "10.0.1.1/32"}
                    ]
                }
            }
            success, err = self.add_flow(s2_id, rule)

        if 'h1' in s1_ports:
            rule = {
                "priority": 40000,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {"instructions": [{"type": "OUTPUT", "port": str(s1_ports['h1'])}]},
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_DST", "ip": "10.0.1.1/32"}
                    ]
                }
            }
            success, err = self.add_flow(s1_id, rule)
        return True


def apply_qos_rules(net):
    manager = ONOSFlowManager()

    # Проверяем подключение к ONOS
    devices, error = manager.get_devices()
    if error:
        return False

    return manager.apply_qos_rules(net)