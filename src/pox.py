import requests
import csv
import time
import logging
import os
from dotenv import load_dotenv
from transactions import deserialize_cv, ClarityValue
from base32_crockford import encode as c32address

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# API base URL for Stacks mainnet
STACKS_API_URL = 'https://api.mainnet.hiro.so'
contract_address = "SP000000000000000000002Q6VF78"
contract_name = "pox-4"
sender = "SP3TRVBX53CN78AS8C3HNTM3GPNDHGA34F9M7MAH2"
api_key = os.getenv('STACKS_API_KEY')

# Parse Clarity value from a hex string
def parse_clarity_value(hex_str):
    if hex_str.startswith('0x'):
        hex_str = hex_str[2:]
    logging.debug(f"Parsing Clarity value from hex string: {hex_str}")
    return deserialize_cv(bytes.fromhex(hex_str))

# Convert value to Clarity Hex
def generate_hex(value):
    hex_value = hex(value)[2:]
    padded_value = hex_value.zfill(33)
    final_hex = '01' + padded_value[1:]
    logging.debug(f"Generated hex for value {value}: {final_hex}")
    return '0x' + final_hex

# Decode Clarity Hex to integer
def decode_hex(value):
    if value.startswith('0x'):
        value = value[2:]
    if value.startswith('01'):
        value = value[2:]
    stripped_value = value.lstrip('0')
    decoded_value = int(stripped_value, 16) if stripped_value else 0
    logging.debug(f"Decoded hex value {value} to integer: {decoded_value}")
    return decoded_value

# Function to get the number of stackers for a specific cycle
def get_no_stackers(value):
    function_name = 'get-reward-set-size'
    url = f"{STACKS_API_URL}/v2/contracts/call-read/{contract_address}/{contract_name}/{function_name}"
    payload = {
        "sender": sender,
        "arguments": [generate_hex(value)]
    }
    headers = {'X-API-KEY': api_key}
    logging.debug(f"Requesting number of stackers for cycle {value} with payload: {payload}")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json().get("result")
        logging.debug(f"Received response for number of stackers: {result}")
        return decode_hex(result)
    else:
        logging.error(f"Error retrieving number of stackers: {response.status_code} {response.text}")
        return None

# Function to get stacker info by cycle and index
def get_stackers_by_cycle(cycle, index):
    function_name = 'get-reward-set-pox-address'
    url = f"{STACKS_API_URL}/v2/contracts/call-read/{contract_address}/{contract_name}/{function_name}"
    payload = {
        "sender": sender,
        "arguments": [generate_hex(cycle), generate_hex(index)]
    }
    headers = {'X-API-KEY': api_key}
    logging.debug(f"Requesting stacker info for cycle {cycle}, index {index} with payload: {payload}")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json().get("result")
        logging.debug(f"Received response for stacker info: {result}")
        if result:
            clarity_value = parse_clarity_value(result)
            if isinstance(clarity_value, bool):
                logging.warning(f"Clarity value is a boolean: {clarity_value}, skipping processing for cycle {cycle}, index {index}")
                return None
            if not isinstance(clarity_value, ClarityValue):
                logging.error(f"Unexpected Clarity value type: {type(clarity_value)}, skipping processing for cycle {cycle}, index {index}")
                return None

            clarity_data = clarity_value.value.data

            # Decoding pox-addr
            pox_addr = clarity_data['pox-addr'].data
            hashbytes_hex = pox_addr['hashbytes'].buffer.hex()
            version_hex = pox_addr['version'].buffer.hex()

            # Decoding signer
            signer = clarity_data['signer']
            signer_hex = signer.buffer.hex() if signer.buffer else 'Signer is missing'

            # Decoding stacker
            stacker = clarity_data['stacker']
            stacker_address = None
            if stacker.type == 10 and stacker.value.type == 5:
                address = stacker.value.address
                stacker_address = c32address(address.version, address.hash160)

            # Ensure Total uSTX is a number, not an object
            total_ustx = str(clarity_data['total-ustx'].value)

            stacker_info = {
                "index": index,
                "cycle": cycle,
                "poxAddrHash": f"0x{hashbytes_hex}",
                "poxAddrVersion": f"0x{version_hex}",
                "signer": f"0x{signer_hex}",
                "ustx": total_ustx,
                "stackerAddress": stacker_address
            }
            logging.debug(f"Parsed stacker info: {stacker_info}")
            return stacker_info
    else:
        logging.error(f"Error parsing response for cycle {cycle}, index {index}: {response.status_code} {response.text}")
    return None

# Main execution
if __name__ == "__main__":
    cycles = [90, 91, 92, 93, 94]  # Array of cycles to iterate over
    stackers_data = []

    for cycle in cycles:
        logging.info(f"Processing cycle: {cycle}")
        number_of_stackers = get_no_stackers(cycle)
        if number_of_stackers is not None:
            for index in range(number_of_stackers):
                stacker_info = get_stackers_by_cycle(cycle, index)
                if stacker_info:
                    stackers_data.append(stacker_info)
                time.sleep(0.5)  # To avoid rate limiting

    # Write the data to CSV
    if stackers_data:
        csv_headers = ["index", "cycle", "poxAddrHash", "poxAddrVersion", "signer", "ustx", "stackerAddress"]
        with open("stackers.csv", "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            for data in stackers_data:
                logging.debug(f"Writing data to CSV: {data}")
                writer.writerow(data)
        logging.info("CSV file successfully written.")
    else:
        logging.info("No stacker data found to write to CSV.")
