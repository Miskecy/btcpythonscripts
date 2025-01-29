# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:12:18 2025

@author: ChangeMe
"""

import requests

def get_transactions_from_address(address):
    """
    Fetch all transactions for a given Bitcoin address using mempool.space API.
    """
    # Public mempool: https://mempool.space/api/address/{address}/txs
    url = f"https://mempool.unstoppableworld.org/api/address/{address}/txs"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Return the list of transactions
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transactions: {e}")
        return None

def extract_public_key_from_transaction(transaction):
    """
    Attempt to extract the public key from a transaction's input script.
    """
    for input_tx in transaction.get("vin", []):
        if "scriptsig" in input_tx:
            scriptsig = input_tx["scriptsig"]
            # The public key might be embedded in the scriptSig (for P2PKH transactions)
            # This is a simplified example and may not work for all cases
            if "21" in scriptsig:  # Check for a compressed public key (33 bytes, 0x21 prefix)
                pubkey_start = scriptsig.find("21") + 2
                pubkey_hex = scriptsig[pubkey_start:pubkey_start + 66]  # 33 bytes in hex
                return pubkey_hex
    return None

def get_public_key_from_address(address):
    """
    Fetch transactions for the address and attempt to extract the public key.
    """
    transactions = get_transactions_from_address(address)
    if not transactions:
        print("No transactions found for this address.")
        return None

    # Iterate through transactions to find the public key
    for tx in transactions:
        public_key = extract_public_key_from_transaction(tx)
        if public_key:
            return public_key

    print("Public key not found in any transaction.")
    return None

if __name__ == "__main__":
    # Get the address from user input
    address = input("Enter the Bitcoin address: ")

    # Fetch the public key
    public_key = get_public_key_from_address(address)

    if public_key:
        print(f"Public Key: {public_key}")
    else:
        print("Could not retrieve the public key.")
