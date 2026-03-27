"""
Модуль для управления flow rules в ONOS через REST API
"""

import requests
import json
import time
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()


class ONOSFlowManager:
    """Класс для управления flow rules в ONOS"""

    def __init__(self, onos_ip='127.0.0.1', port=8181, user='karaf', password='karaf'):
        self.base_url = f"http://{onos_ip}:{port}/onos/v1"
        self.auth = HTTPBasicAuth(user, password)
        self.headers = {'Content-Type': 'application/json'}

    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, auth=self.auth, timeout=5)
            elif method == 'POST':
                response = requests.post(url, auth=self.auth,
                                         data=json.dumps(data),
                                         headers=self.headers,
                                         timeout=5)
            elif method == 'DELETE':
                response = requests.delete(url, auth=self.auth, timeout=5)
            else:
                return None, f"Unsupported method: {method}"

            return response, None
        except requests.exceptions.ConnectionError:
            return None, f"Cannot connect to ONOS at {self.base_url}"
        except requests.exceptions.Timeout:
            return None, "Connection timeout"
        except Exception as e:
            return None, str(e)

    def get_devices(self):
        response, error = self._make_request('GET', 'devices')
        if error:
            return None, error
        if response.status_code == 200:
            return response.json().get('devices', []), None
        return None, f"Failed to get devices: {response.status_code}"

    def get_ports(self, device_id):
        response, error = self._make_request('GET', f'devices/{device_id}/ports')
        if error:
            return None, error
        if response.status_code == 200:
            return response.json().get('ports', []), None
        return None, f"Failed to get ports: {response.status_code}"

    def add_flow(self, device_id, flow_rule):
        url = f"{self.base_url}/flows/{device_id}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=headers,
                data=json.dumps(flow_rule),
                timeout=5
            )
            if response.status_code in [200, 201]:
                return True, None
            return False, f"Failed to add flow: {response.status_code} - {response.text}"
        except Exception as e:
            return False, str(e)

    def delete_all_flows(self, device_id):
        response, error = self._make_request('DELETE', f'flows/{device_id}')
        if error:
            return False, error
        if response.status_code == 204:
            return True, None
        return False, f"Failed to delete flows: {response.status_code}"

    def discover_ports(self, net):
        ports_info = {}

        s1_ports = {}
        for node_name, intf in net['s1'].nameToIntf.items():
            if node_name == 'lo':
                continue
            port_num = net['s1'].ports[intf]
            link = intf.link
            if link:
                if link.intf1.node.name == 's1':
                    other_node = link.intf2.node.name
                else:
                    other_node = link.intf1.node.name
                s1_ports[other_node] = port_num

        s2_ports = {}
        for node_name, intf in net['s2'].nameToIntf.items():
            if node_name == 'lo':
                continue
            port_num = net['s2'].ports[intf]
            link = intf.link
            if link:
                if link.intf1.node.name == 's2':
                    other_node = link.intf2.node.name
                else:
                    other_node = link.intf1.node.name
                s2_ports[other_node] = port_num

        ports_info['s1'] = s1_ports
        ports_info['s2'] = s2_ports
        return ports_info

    def add_isolation_rules(self, net):

        ports = self.discover_ports(net)

        s1_ports = ports['s1']  # {'h1': , 'h2': , 's2': }
        s2_ports = ports['s2']  # {'gw': , 'h3': , 'h4': , 's1': }

        print(f"s1 ports: {s1_ports}")
        print(f"s2 ports: {s2_ports}")

        s1_id = 'of:0000000000000001'
        s2_id = 'of:0000000000000002'

        s1_rules = [
            {
                "priority": 50000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "FLOOD"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0806"}
                    ]
                }
            },
            {
                "priority": 45000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": []
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.0/24"},
                        {"type": "IPV4_DST", "ip": "10.0.2.0/24"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "FLOOD"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.0/24"},
                        {"type": "IPV4_DST", "ip": "10.0.1.0/24"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": str(s1_ports['s2'])}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.0/24"},
                        {"type": "IPV4_DST", "ip": "10.0.1.254/32"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "FLOOD"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.1.254/32"},
                        {"type": "IPV4_DST", "ip": "10.0.1.0/24"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": str(s1_ports['s2'])}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_DST", "ip": "10.0.2.254/32"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s1_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": str(s1_ports['s2'])}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.2.254/32"},
                        {"type": "IPV4_DST", "ip": "10.0.2.0/24"}
                    ]
                }
            }
        ]

        s2_rules = [
            {
                "priority": 50000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s2_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "FLOOD"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0806"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s2_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "FLOOD"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.2.0/24"},
                        {"type": "IPV4_DST", "ip": "10.0.2.0/24"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s2_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "3"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_DST", "ip": "10.0.2.254/32"}
                    ]
                }
            },
            {
                "priority": 40000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": s2_id,
                "treatment": {
                    "instructions": [
                        {"type": "OUTPUT", "port": "FLOOD"}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},
                        {"type": "IPV4_SRC", "ip": "10.0.2.254/32"}
                    ]
                }
            }
        ]

        for device_id in [s1_id, s2_id]:
            self.delete_all_flows(device_id)

        time.sleep(1)

        success_count = 0
        for rule in s1_rules + s2_rules:
            success, error = self.add_flow(rule['deviceId'], rule)
            if success:
                success_count += 1

        return success_count > 0


def apply_rules(net=None):

    manager = ONOSFlowManager()

    devices, error = manager.get_devices()
    if error:
        return False

    if net is None:
        return False

    success = manager.add_isolation_rules(net)

    return success