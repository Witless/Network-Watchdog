

# Network Watchdog

Network Watchdog is a Python application designed to monitor and manage network states dynamically. Inspired by the functionality of the **[Hot Standby Router Protocol (HSRP)](https://www.cisco.com/c/en/us/support/docs/ip/hot-standby-router-protocol-hsrp/9234-hsrpguidetoc.html)**, this tool ensures network reliability by periodically retrieving network states, detecting failures, and cloning network configurations when necessary.

## Features

- **Dynamic Network State Monitoring**: Periodically retrieves the current state of the network using the RYU controller.
- **Failure Detection**: Automatically detects if the RYU controller is unreachable or if the network state is empty.
- **Network Cloning**: Clones the last known network state to ensure continuity in case of failures.

## How It Works

1. **Initialization**: The application starts by clearing the `last_state.json` file and setting up the monitoring loop.
2. **Periodic Retrieval**: Every 30 seconds, the application sends a heartbeat to the RYU controller. 
3. **Failure Handling**: If the RYU controller is unreachable or returns an empty response, the application clones the last known network state to maintain network functionality.
The cloned network will have the switches, its flows and the links between them but not the hosts as this information.
   isn't provided by the RYU Northbound API 
4. **State Updates**: The `new_state.json` file is copied to `last_state.json` after every successful retrieval to keep the state up-to-date.

## Requirements

**Python3** ( requests >= 2.31.0, mininet >= 2.3.0)

**Mininet**

**RYU Controller** 


## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Network-Watchdog
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Mininet and RYU Controller are installed and running.

## Usage

Start by running a Mininet instance and the RYU controller in a separate environment, I used comnetsemu.

First initialize the RYU controller:
```bash
ryu-manager --observe-links simple_switch_13.py ofctl_rest.py rest_topology.py ws_topology.py
```

Two example networks are provided in the `examples` directory, which can be used to test the application run any of these or your own
in the same environment as the RYU controller.

```bash
sudo python3 create_net.py
```

For running the main application move to a different environment of the one you have been
working on in the last steps (in my case I used my local desktop). 

Update the `main.py` file with the correct RYU controller IP address and port modifying the `RYU_CONTROLLER_URL` variable. 

Ensure here you have installed all the requirements mentioned before and then run the app:

```bash
sudo python3 main.py
```

While the app is running you can play in the separate environment with  Mininet or any other tool to modify the network, for example, you can add switches, remove links or add flows. 

You will see these changes are noted in the every 30 seconds check. 

At one point you can stop the RYU controller or disconnect it from the Mininet environment.

The application will detect this and clone the last known state of the network, which will be saved in `last_state.json`.

## Frequently Asked Questions (FAQ)

**Why using sudo everywhere?**: The application uses Mininet, which requires root access.

**Is there any License?**: Yes, this project is licensed under The Unlicense.

**Can I use this in production?**: I wouldn't recommend. It may require special adaptability for production use.

**I still have questions**: Feel free to open an issue or contact me directly.

## Schema of the Network State

The network state is in JSON format, its schema is:

```json
{
  "network": {
    "nodes": [
      {
        "id": "",
        "type": "",
        "ip": "",
        "ports": [
          {
            "port_no": "",
            "status": "",
            "mac": ""
          }
        ],
        "flows": [
          {
            "flow_id": "",
            "in_port": "",
            "src_ip": "",
            "dst_ip": "",
            "byte_count": "",
            "packet_count": "",
            "priority": "",
            "timestamp": "",
            "actions": ""
          }
        ]
      }
    ],
    "links": [
      {
        "id": "",
        "src": {
          "node_id": "",
          "port_no": ""
        },
        "dst": {
          "node_id": "",
          "port_no": ""
        },
        "status": ""
      }
    ],
    "last_updated": ""
  }
}
```



