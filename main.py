"""
RUN WITH SUDO
Because the script uses the mininet package which requires root privileges to set up a new network it is
mandatory to run this script with superuser privileges.
"""

import json
import time
import requests
from functions import retrieve, test, clone

RYU_CONTROLLER_URL = "http://localhost:8080"


def main():
    response = requests.get(f"{RYU_CONTROLLER_URL}/stats/switches")
    if response.status_code != 200 or not response.json():
        print("Can't retrieve the network, shutting down...")
        return  # Exit if the network is not reachable

    with open("./states/last_state.json", "w") as file:
        json.dump({"network": ""}, file, indent=2)

    while True:

        retrieve(RYU_CONTROLLER_URL)

        test()

        # If RYU_CONTROLLER_URL/stats/switches returns error or empty, then run clone()
        response = requests.get(f"{RYU_CONTROLLER_URL}/stats/switches")
        if response.status_code != 200 or not response.json():
            print("RYU controller is not running. Cloning the network.")
            clone()

        # Copy new_state.json to last_state.json
        with open("./states/new_state.json", "r") as file:
            new_state = json.load(file)
        with open("./states/last_state.json", "w") as file:
            json.dump(new_state, file, indent=2)

        time.sleep(30) # Sleep for 30 seconds before the next iteration, this number can be increased or lowered


if __name__ == "__main__":
    main()
