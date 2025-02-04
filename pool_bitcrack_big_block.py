# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 17:03:38 2025
@author: Chikyuujin
"""
import requests
import os
import subprocess
import time
from datetime import datetime
from colorama import Fore, Style, init

API_URL = "https://bitcoinpuzzles.io/api/big_block"
POOL_TOKEN = "9ea47c6b018df523c8a2b7e94f03da16c75049e8f3ba2d61b79c5e0438a27fd0"
ADDITIONAL_ADDRESS = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"

# Initialize colorama
init(autoreset=True)

# --------------------------------------------------------------------------------------------------------------------------------------------

def clear_screen():
    """Clears the terminal screen to provide a clean output view."""
    os.system("cls" if os.name == "nt" else "clear")

# --------------------------------------------------------------------------------------------------------------------------------------------

def logger(level, message):
    """
    Logs a message with a timestamp and colored log level.
    
    Args:
        level (str): The log level (e.g., "Info", "Warning", "Error", "Success", "KEYFOUND").
        message (str): The message to log.
    """
    # Get the current date and time
    current_time = datetime.now()
    
    # Format the date and time as [YYYY-MM-DD.HH:MM:SS]
    formatted_time = current_time.strftime("[%Y-%m-%d.%H:%M:%S]")
    
    # Map log levels to colors
    color_map = {
        "Info": Fore.LIGHTBLUE_EX,
        "Warning": Fore.LIGHTYELLOW_EX,
        "Error": Fore.LIGHTRED_EX,
        "Success": Fore.LIGHTGREEN_EX,
        "KEYFOUND": Fore.LIGHTMAGENTA_EX,
        "Timer": Fore.LIGHTYELLOW_EX
    }
    
    # Get the color for the log level (default to white if not found)
    color = color_map.get(level, Fore.WHITE)
    
    # Print the formatted message with color
    print(f"{formatted_time} {color}[{level}]{Style.RESET_ALL} {message}")

# --------------------------------------------------------------------------------------------------------------------------------------------

def fetch_block_data():
    """Fetches the block data from the API.
    
    Sends a GET request to the API to retrieve information about the current block.
    If successful, it returns the block data in JSON format; otherwise, it prints an error.
    """
    headers = {"pool-token": POOL_TOKEN}
    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger("Error", f"Error fetching block: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        logger("Error", f"Request Error {e}")
        return None

# --------------------------------------------------------------------------------------------------------------------------------------------

def save_addresses_to_file(addresses, additional_address, filename="in.txt"):
    """Saves a list of addresses and the additional address to a file.
    
    The function takes a list of addresses and appends the additional address to the file.
    Each address is saved in a new line in the 'in.txt' file.
    """
    try:
        with open(filename, "w") as file:
            for address in addresses:
                file.write(address + "\n")
            file.write(additional_address + "\n")
        logger("Info", f"Addresses saved successfully to '{filename}'.")
    except Exception as e:
        logger("Error", f"Error saving address: {e}")

# --------------------------------------------------------------------------------------------------------------------------------------------

def save_progress(current_part, total_parts, start_hex, end_hex, filename="progress.txt"):
    """Saves the current progress to a file."""
    try:
        with open(filename, "w") as file:
            file.write(f"{current_part}\n{total_parts}\n{start_hex}\n{end_hex}\n")
        logger("Success", f"Progress saved to '{filename}'.")
    except Exception as e:
        logger("Error", f"Error saving progress: {e}")

# --------------------------------------------------------------------------------------------------------------------------------------------

def load_progress(start_hex, end_hex, filename="progress.txt"):
    """Loads the progress from a file if it matches the current range."""
    if not os.path.exists(filename):
        return 0, 0  # No progress file exists

    try:
        with open(filename, "r") as file:
            lines = file.readlines()
            if len(lines) < 4:
                return 0, 0  # Invalid progress file

            saved_current_part = int(lines[0].strip())
            saved_total_parts = int(lines[1].strip())
            saved_start_hex = lines[2].strip()
            saved_end_hex = lines[3].strip()

            # Check if the saved range matches the current range
            if saved_start_hex == start_hex and saved_end_hex == end_hex:
                logger("Info", f"Resuming from part {saved_current_part + 1}/{saved_total_parts}.")
                return saved_current_part, saved_total_parts
            else:
                logger("Info", "Range mismatch. Deleting old progress file.")
                os.remove(filename)
                return 0, 0
    except Exception as e:
        logger("Error", f"Error loading progress: {e}")
        return 0, 0

# --------------------------------------------------------------------------------------------------------------------------------------------

def clear_file(filename):
    """Clears the content of a specified file.
    
    This function opens the file in write mode and empties its contents by not writing anything.
    It then prints a success message or an error message if something goes wrong.
    """
    try:
        with open(filename, "w"):
            pass
        logger("Info", f"File '{filename}' cleared successfully.")
    except Exception as e:
        logger("Error", f"Error clearing file '{filename}': {e}")

# --------------------------------------------------------------------------------------------------------------------------------------------

def split_and_run(start_hex, end_hex, num_parts=10):
    """Divides the keyspace into num_parts and runs each part sequentially."""
    try:
        # Check if the range has changed and delete progress file if necessary
        if os.path.exists("progress.txt"):
            with open("progress.txt", "r") as file:
                lines = file.readlines()
                if len(lines) >= 4:
                    saved_start_hex = lines[2].strip()
                    saved_end_hex = lines[3].strip()
                    if saved_start_hex != start_hex or saved_end_hex != end_hex:
                        logger("Info", "Range changed. Deleting old progress file.")
                        os.remove("progress.txt")
                        
        start = int(start_hex, 16)
        end = int(end_hex, 16)
    except ValueError as e:
        logger("Error", f"Invalid start or end hex value: {e}")
        return False

    if start > end:
        logger("Error", "Start value is greater than end value.")
        return False

    total = end - start + 1
    if total < 1:
        logger("Error", "Invalid keyspace range (start > end).")
        return False

    # Load progress if available
    current_part, total_parts = load_progress(start_hex, end_hex)
    #total = total_parts if total_parts else total
    if current_part >= num_parts:
        logger("Info", "All parts already processed.")
        return False
    
    # Adjust num_parts if total is smaller than num_parts
    if total < num_parts:
        num_parts = total

    part_size = total // num_parts
    remainder = total % num_parts


    current_start = start + (current_part * part_size)
    if current_part < remainder:
        current_start += current_part
    else:
        current_start += remainder

    # Process each part sequentially
    for i in range(current_part, num_parts):
        current_part_size = part_size
        if i < remainder:
            current_part_size += 1

        current_end = current_start + current_part_size - 1
        if current_end > end:
            current_end = end

        part_start_hex = hex(current_start)[2:]
        part_end_hex = hex(current_end)[2:]

        logger("Info", f"Processing part {i+1}/{num_parts}: {part_start_hex} to {part_end_hex}")
        run_program(part_start_hex, part_end_hex)

        # Save progress after each part
        save_progress(i, num_parts, start_hex, end_hex)

        # After each part, we check the output, but we don't stop the loop yet
        current_start = current_end + 1
        if current_start > end:
            break

        # Wait xx seconds before starting the next part
        time.sleep(10)
        logger("Timer", "Waiting 10 seconds before starting the next part.")

    # After all parts are processed, check the output file
    logger("Info", "All parts processed. Now checking the output file for the solution.")
    if process_out_file():
        logger("Success", "Solution found in output file.")
        # Delete progress file after successful completion
        if os.path.exists("progress.txt"):
            os.remove("progress.txt")
        return True
    else:
        logger("Warning", "Solution not found in output file.")

    return False

# --------------------------------------------------------------------------------------------------------------------------------------------

def run_program(start, end):
    """Runs the external cuBitCrack program with the given keyspace.
    
    This function generates a keyspace based on the provided start and end range, 
    then executes the cuBitCrack program with specific options to attempt cracking the private keys.
    """
    keyspace = f"{start}:{end}"
    command = [
        "sudo", "unshare", "--net",
        "./cuBitCrack",
        "-t", "256",					# Increased threads per block
        "-b", "128",					# Adjusted blocks based on GPU compute units
        "-p", "64", 					# Increased keys per thread
        "-c",							# Search for compressed keys
        "-i", "in.txt", 				# Path for input file
        "-o", "out.txt",				# Path for output file
        "--keyspace", keyspace, 		# Keyspace to be cracked
    ]
    # command = [
    #     "sudo", "unshare", "--net",
    #     "./cuBitCrack",
    #     "-t", "256",					# Increased threads per block
    #     "-b", "208",					# Adjusted blocks based on GPU compute units
    #     "-p", "512", 					# Increased keys per thread
    #     "-c",							# Search for compressed keys
    #     "-i", "in.txt", 				# Path for input file
    #     "-o", "out.txt",				# Path for output file
    #     "--keyspace", keyspace, 		# Keyspace to be cracked
    # ]
    try:
        logger("Info", f"Running with keyspace {keyspace}")
        subprocess.run(command, check=True)
        logger("Success", "Script loaded successfully")
    except subprocess.CalledProcessError as e:
        logger("Error", f"Error running script: {e}")
    except Exception as e:
        logger("Error", f"Error exception: {e}")

# --------------------------------------------------------------------------------------------------------------------------------------------

def post_private_keys(private_keys):
    """Sends private keys to the API in batches of up to 10 keys.
    
    The private keys are sent in JSON format in a POST request. Each batch of keys is logged before it is sent.
    The function prints the response from the API or any error messages.
    """
    headers = {
        "pool-token": POOL_TOKEN,
        "Content-Type": "application/json"
    }
    data = {"privateKeys": private_keys}
    
    logger("Info", f"Sending the array of private keys ({len(private_keys)} / 10)")
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            logger("Success", "Private keys sent successfully.")
        else:
            logger("Error", f"Error sending private keys: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logger("Error", f"Error making the POST request: {e}")

# --------------------------------------------------------------------------------------------------------------------------------------------

def process_out_file(out_file="out.txt", in_file="in.txt", additional_address=ADDITIONAL_ADDRESS):
    """Processes the 'out.txt' and 'in.txt' files, extracts the private keys, and sends them to the API.
    
    This function checks if the 'out.txt' and 'in.txt' files exist, reads the private keys and addresses from the files, 
    matches them, and sends batches of 10 private keys to the API. If the private key for the additional address is found, 
    the program stops early.
    """
    if not os.path.exists(out_file):
        logger("Warning", f"File '{out_file}' not found.")
        return False

    if not os.path.exists(in_file):
        logger("Warning", f"File '{in_file}' not found.")
        return False

    private_keys = {}
    addresses = []
    found_additional_address = False

    try:
        # Reading the addresses from the in.txt file
        with open(in_file, "r") as file:
            addresses = [line.strip() for line in file if line.strip()]
        
        # Removing the additional address to avoid inconsistency
        if additional_address in addresses:
            addresses.remove(additional_address)

        # Reading the addresses and private keys from the out.txt file
        with open(out_file, "r") as file:
            current_address = None
            for line in file:
                parts = line.split()  # Split the line into parts by whitespace                
                
                if len(parts) >= 3:  # Ensure that the line contains at least 3 parts (address, something, private key)
                    current_address = parts[0].strip()  # The first string (address)
                    
                    # Makeshift for BitCrack Bug
                    if len(current_address) < 34:
                        # Prefix with '1' until the length is 34
                        current_address = current_address.rjust(34, '1')

                    private_key = parts[1].strip()  # The third string (private key)                                     
                    
                    # Store the private key with the address as the key in the dictionary
                    private_keys[current_address] = "0x"+private_key
                    
                    # Checking if it is the key for the additional address
                    if current_address == additional_address:
                        found_additional_address = True

        # If the private key for the additional address was found
        if found_additional_address:
            logger("KEYFOUND", "Private key for the additional address found! Stopping the program.")
            logger("KEYFOUND", f"{private_keys.get(additional_address)}")
            try:
                with open('KEYFOUND.txt', "w") as file:
                    file.write(private_keys.get(additional_address) + "\n")
                    
                logger("KEYFOUND", f"Addresses saved successfully to KEYFOUND.txt")
            except Exception as e:
                logger("KEYFOUND Error", f"Error saving address: {e}")
                    
            return True

        # Checking if the number of private keys matches the number of addresses
        if len(private_keys) != len(addresses):
            logger("Error", f"Number of private keys ({len(private_keys)}) does not match the number of addresses ({len(addresses)}).")
            clear_file(out_file)
            return False
        
        # Sorting the private keys in the same order as the addresses in in.txt
        ordered_private_keys = []
        for addr in addresses:
            # Check for both the original address and the modified address
            if addr in private_keys:
                ordered_private_keys.append(private_keys[addr])
            else:
                # Makeshift for BitCrack Bug: Create a modified address if length is less than 34
                modified_addr = addr.rjust(34, '1') if len(addr) < 34 else addr
                if modified_addr in private_keys:
                    ordered_private_keys.append(private_keys[modified_addr])
                else:
                    logger("Warning", f"Address '{addr}' not found in private keys.")
        
        # Sending the private keys in batches of 10
        for i in range(0, len(ordered_private_keys), 10):
            batch = ordered_private_keys[i:i + 10]
            if len(batch) == 10:
                post_private_keys(batch)
                #print(f"[SUCCESS]: {len(batch)}")
            else:                
                logger("Warning", f"Batch with less than 10 keys ignored: {len(batch)}")

    except Exception as e:
        logger("Error", f"processing files: {e}")

    # Clear the out.txt file after processing
    #return True
    clear_file(out_file)
    return False

# --------------------------------------------------------------------------------------------------------------------------------------------

# Main loop
if __name__ == "__main__":
    while True:
        #clear_screen()  # Clear the screen to prepare for the next iteration
        block_data = fetch_block_data()  # Fetch the block data (addresses and range)
        
        if block_data:
            addresses = block_data.get("checkwork_addresses", [])
            if addresses:
                save_addresses_to_file(addresses, ADDITIONAL_ADDRESS)
                
                # Extracting start and end from the range
                range_data = block_data.get("range", {})
                start = range_data.get("start", "").replace("0x", "")  # Clean the hex string
                end = range_data.get("end", "").replace("0x", "")  # Clean the hex string
                
                if start and end:
                    logger("Info", f"Starting to split and process the range from {start} to {end}.")
                    solution_found = split_and_run(start, end, num_parts=20)  # Run the keyspace splitting logic

                    if solution_found:
                        logger("Success", "Solution found during processing.")
                        break  # Exit the loop if the solution is found
                    else:
                        logger("Info", "Solution not found in this run.")
                else:
                    logger("Info", "Start or End not found in the range.")
            else:
                logger("Warning", "No addresses found in the block.")
        else:
            logger("Error", "Error fetching block data.")

        # Wait xx seconds before restarting the loop
        #time.sleep(5)
