import os
import requests
import json
from typing import Any, Dict, List, Tuple
from datetime import datetime
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController
from mininet.cli import CLI


def get_switches(ryu_controller_url):
    response = requests.get(f"{ryu_controller_url}/v1.0/topology/switches")
    return response.json()


def get_hosts(ryu_controller_url):
    """This endpoint, even though it's present in the rest_topology.py module, doesn't currently work.
    However, the logic for fetching Host information has been created as well as the logic for adding it to the
    cloned network"""
    response = requests.get(f"{ryu_controller_url}/v1.0/topology/hosts")
    return response.json()


def get_links(ryu_controller_url):
    response = requests.get(f"{ryu_controller_url}/v1.0/topology/links")
    return response.json()


def get_flows(dpid, ryu_controller_url):
    response = requests.get(f"{ryu_controller_url}/stats/flow/{dpid}")
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON response for DPID {dpid}")
            return {}
    else:
        print(f"Error: Failed to fetch flows for DPID {dpid}, Status Code: {response.status_code}")
        return {}


def retrieve(ryu_controller_url="http://localhost:8080"):
    network = {"nodes": [], "links": []}

    switches = get_switches(ryu_controller_url)
    for switch in switches:
        dpid = str(int(switch['dpid']))  # Remove leading zeros
        switch_info = {
            "id": f"{dpid}",
            "type": "switch",
            "ip": switch.get('ip', 'N/A'),
            "ports": [
                {
                    "port_no": port['port_no'],
                    "status": port.get('state', 'unknown'),  # Use 'unknown' as a default value
                    "mac": port['hw_addr']
                }
                for port in switch['ports']
            ],
            "flows": []
        }
        flows = get_flows(dpid, ryu_controller_url)
        for flow in flows.get(dpid, []):
            switch_info["flows"].append({
                "flow_id": flow['cookie'],
                "in_port": flow['match'].get('in_port', '0'),
                "src_ip": flow['match'].get('ipv4_src', '0'),
                "dst_ip": flow['match'].get('ipv4_dst', '0'),
                "byte_count": flow['byte_count'],
                "packet_count": flow['packet_count'],
                "priority": flow['priority'],
                "timestamp": datetime.now().isoformat(),
                "actions": flow.get('actions', {}).get('OUTPUT', 'NORMAL')
            })
        network["nodes"].append(switch_info)

    hosts = get_hosts(ryu_controller_url)
    for index, host in enumerate(hosts):
        host_info = {
            "id": f"{index + 1}",
            "type": "host",
            "ip": host['ipv4'][0] if host['ipv4'] else 'N/A',
            "mac": host['mac']
        }
        network["nodes"].append(host_info)

    links = get_links(ryu_controller_url)
    for link in links:
        # Clean up node IDs for Mininet compatibility
        src_node_id = f"s{int(link['src']['dpid'])}"  # Convert to 's1', 's2' ...
        dst_node_id = f"s{int(link['dst']['dpid'])}"

        link_info = {
            "id": f"link{link['src']['dpid']}_{link['dst']['dpid']}",
            "src": {"node_id": src_node_id, "port_no": link['src']['port_no']},
            "dst": {"node_id": dst_node_id, "port_no": link['dst']['port_no']},
            "status": "active"
        }
        network["links"].append(link_info)

    # Add timestamp for logging purposes
    network["last_updated"] = datetime.now().isoformat()

    with open("./states/new_state.json", "w") as file:
        json.dump({"network": network}, file, indent=2)


def compare_dicts(old: Dict[str, Any], new: Dict[str, Any], path="") -> List[str]:
    diffs = []

    # Here we ignore the "last_updated" key, as otherwise we would get at least this change when the heartbeat is sent
    ignored_keys = {"last_updated"}

    all_keys = set(old.keys()) | set(new.keys())
    for key in all_keys:
        if key in ignored_keys:
            continue  # Skip ignored keys
        current_path = f"{path}.{key}" if path else key
        if key not in old:
            diffs.append(f"New key added at '{current_path}': {new[key]}")
        elif key not in new:
            diffs.append(f"Key removed at '{current_path}': {old[key]}")
        else:
            diffs.extend(compare_values(old[key], new[key], current_path))
    return diffs


def compare_lists(old: List[Any], new: List[Any], path="") -> List[str]:
    diffs = []

    # If lists elements are dictionaries and 'id' key exists this can be used, if elements don't have "id", fall back to sequential compare
    if all(isinstance(i, dict) for i in old + new):
        # Build lookup dictionaries (using the "id" field)
        old_lookup = {item.get("id"): item for item in old if "id" in item}
        new_lookup = {item.get("id"): item for item in new if "id" in item}

        all_ids = set(old_lookup.keys()) | set(new_lookup.keys())
        for id_key in all_ids:
            new_path = f"{path}[id={id_key}]"
            if id_key not in old_lookup:
                diffs.append(f"New element added at '{new_path}': {new_lookup[id_key]}")
            elif id_key not in new_lookup:
                diffs.append(f"Element removed at '{new_path}': {old_lookup[id_key]}")
            else:
                diffs.extend(compare_dicts(old_lookup[id_key], new_lookup[id_key], new_path))
    else:
        # Fall back: use simple list difference (this assumes order matters)
        if old != new:
            diffs.append(f"List changed at '{path}': was {old} and is now {new}")

    return diffs


def compare_values(old: Any, new: Any, path="") -> List[str]:
    diffs = []
    if type(old) != type(new):
        diffs.append(f"Type mismatch at '{path}': {type(old).__name__} vs {type(new).__name__}")
    elif isinstance(old, dict):
        diffs.extend(compare_dicts(old, new, path))
    elif isinstance(old, list):
        diffs.extend(compare_lists(old, new, path))
    else:
        if old != new:
            diffs.append(f"Value changed at '{path}': '{old}' -> '{new}'")
    return diffs


def compare_network_states(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Tuple[bool, List[str]]:
    differences = compare_dicts(old_state, new_state)
    return (len(differences) > 0, differences)


def test():
    old_state_json = open("./states/last_state.json").read()

    new_state_json = open("./states/new_state.json").read()

    old_state = json.loads(old_state_json)
    new_state = json.loads(new_state_json)

    # Compare states
    has_changed, differences = compare_network_states(old_state, new_state)
    # Add timestamp to show on console
    current_time = datetime.now().strftime("%H:%M:%S")

    if has_changed:
        print(f"[{current_time}] Differences detected:")
        for diff in differences:
            print("-", diff)
    else:
        print(f"[{current_time}] No changes detected.")


def clone():
    with open("states/last_state.json", "r") as file:
        data = json.load(file)

    network_data = data["network"]

    # Create a network
    net = Mininet(controller=Controller, switch=OVSSwitch)
    net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6633)

    node_map = {}  # Map to store nodes
    for node in network_data["nodes"]:
        if node["type"] == "switch":
            switch = net.addSwitch(f"s{node['id']}")
            node_map[f"s{node['id']}"] = switch
        elif node["type"] == "host":
            host = net.addHost(f"h{node['id']}", mac=node["mac"], ip=node["ip"] if node["ip"] != "N/A" else None)
            node_map[f"h{node['id']}"] = host

    for link in network_data["links"]:
        src_id = link["src"]["node_id"].replace("switch", "").replace("host", "")
        dst_id = link["dst"]["node_id"].replace("switch", "").replace("host", "")

        src_node = node_map.get(src_id)
        dst_node = node_map.get(dst_id)

        if src_node and dst_node:
            net.addLink(src_node, dst_node)
        else:
            print(f"Warning: Link skipped due to missing nodes: {src_id} -> {dst_id}")

    net.start()

    # Add flows to switches
    for node in network_data["nodes"]:
        if node["type"] == "switch":
            switch = node_map.get(f"s{node['id']}")
            if switch:
                for flow in node.get("flows", []):
                    in_port = flow.get("in_port", "0")
                    src_ip = flow.get("src_ip", "0")
                    dst_ip = flow.get("dst_ip", "0")
                    out_port = flow.get("out_port", "NORMAL")  # Default to 'NORMAL' if 'out_port' is missing
                    actions = f"output:{out_port}"

                    flow_cmd = f"table=0,priority={flow['priority']}"
                    if in_port != "0":
                        flow_cmd += f",in_port={in_port}"
                    if src_ip != "0":
                        flow_cmd += f",ip,nw_src={src_ip},nw_dst={dst_ip}"
                    if actions:
                        flow_cmd += f",actions={actions}"
                    os.system(f"sudo ovs-ofctl add-flow {switch.name} '{flow_cmd}'")

    CLI(net)

    net.stop()
