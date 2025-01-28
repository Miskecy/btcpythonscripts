# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 17:03:38 2025
@author: ChangeMe
"""
import hashlib
import base58
import ecdsa
import bech32
import requests
import time
import secrets

def generate_btc_private_key():
    """
    Generate a cryptographically secure random private key for Bitcoin.
    
    Returns:
    - hex_private_key: Private key as a 64-character hexadecimal string
    - wif_private_key: Wallet Import Format (WIF) encoded private key
    """
    # Generate 32 random bytes (256 bits)
    private_key_bytes = secrets.token_bytes(32)
    
    # Convert to hexadecimal
    hex_private_key = private_key_bytes.hex()
    
    # Optional: Convert to Wallet Import Format (WIF)
    # This requires additional libraries like 'base58' and 'ecdsa'
    # Placeholder for WIF conversion
    
    return hex_private_key

def generate_private_key(random_string):
    return hashlib.sha256(random_string.encode()).digest()

def private_key_to_public_key(private_key):
    signing_key = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    verifying_key = signing_key.get_verifying_key()
    return b'\x04' + verifying_key.to_string()

def private_key_to_wif(private_key):
    # Add version byte (0x80 for mainnet) and compression byte
    extended_key = b'\x80' + private_key + b'\x01'
    
    # Double SHA256 checksum
    checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
    
    # Encode to Base58
    return base58.b58encode(extended_key + checksum).decode()

def legacy_uncompressed_address(public_key):
    ripemd = hashlib.new('ripemd160')
    ripemd.update(hashlib.sha256(public_key).digest())
    network_hash = b'\x00' + ripemd.digest()
    checksum = hashlib.sha256(hashlib.sha256(network_hash).digest()).digest()[:4]
    return base58.b58encode(network_hash + checksum).decode()

def legacy_compressed_address(public_key):
    # Convert public key to compressed format
    x_coordinate = public_key[1:33]
    y_coordinate = public_key[33:65]
    
    # Determine compressed prefix based on y coordinate's parity
    compressed_prefix = b'\x02' if int(y_coordinate[-1]) % 2 == 0 else b'\x03'
    compressed_key = compressed_prefix + x_coordinate
    
    # Hash compressed key
    ripemd = hashlib.new('ripemd160')
    ripemd.update(hashlib.sha256(compressed_key).digest())
    
    # Add network byte and create checksum
    network_hash = b'\x00' + ripemd.digest()
    checksum = hashlib.sha256(hashlib.sha256(network_hash).digest()).digest()[:4]
    
    # Encode to Base58
    return base58.b58encode(network_hash + checksum).decode()

def segwit_address(public_key):
    compressed_key = public_key[:33] if len(public_key) > 33 else public_key
    ripemd = hashlib.new('ripemd160')
    ripemd.update(hashlib.sha256(compressed_key).digest())
    
    # Convert ripemd digest to 5-bit groups for bech32 encoding
    five_bit_groups = bech32.convertbits(ripemd.digest(), 8, 5)
    return bech32.bech32_encode('bc', [0] + five_bit_groups)

def taproot_address(public_key):
    # Ensure compressed public key
    if len(public_key) > 33:
        x_coordinate = public_key[1:33]
        y_coordinate = public_key[33:65]
        is_even = int(y_coordinate[-1]) % 2 == 0
        compressed_prefix = b'\x02' if is_even else b'\x03'
        compressed_key = compressed_prefix + x_coordinate
    else:
        compressed_key = public_key

    # Use x-only pubkey (remove prefix byte)
    x_only_pubkey = compressed_key[1:]

    # Perform BIP340 Taproot key tweaking
    # Hash the x-only public key
    taproot_tweak = hashlib.sha256(b'\x00' + x_only_pubkey).digest()
    
    # Convert to 5-bit groups for bech32 encoding
    five_bit_groups = bech32.convertbits(taproot_tweak, 8, 5)
    
    # Encode as Taproot address (witness version 1)
    return bech32.bech32_encode('bc', [1] + five_bit_groups)

def check_and_save_balance(addresses, private_key, private_key_to_wif):
    results = {}
    for addr_type, address in addresses.items():
        try:
            response = requests.get(f'https://mempool.unstoppableworld.org/api/address/{address}')
            data = response.json()
            
            confirmed_balance = data['chain_stats']['funded_txo_sum'] - data['chain_stats']['spent_txo_sum']
            unconfirmed_balance = data['mempool_stats']['funded_txo_sum'] - data['mempool_stats']['spent_txo_sum']
            
            results[addr_type] = {
                'confirmed': confirmed_balance,
                'unconfirmed': unconfirmed_balance
            }
        except Exception as e:
            results[addr_type] = f"Error: {e}"
    
    # Check if any balance is higher than 0
    for addr_type, balance_info in results.items():
        if isinstance(balance_info, dict) and (balance_info['confirmed'] > 0 or balance_info['unconfirmed'] > 0):
            filename = f"{private_key.hex()}.txt"
            with open(filename, 'w') as f:
                f.write(f"Private Key (Hex): {private_key.hex()}\n")
                f.write(f"Private Key (WIF): {private_key_to_wif(private_key)}\n")
                f.write(f"Address Type: {addr_type}\n")
                f.write(f"Address: {addresses[addr_type]}\n")
                f.write(f"Confirmed Balance: {balance_info['confirmed']}\n")
                f.write(f"Unconfirmed Balance: {balance_info['unconfirmed']}\n")
    
    return results

def continuous_scan():
    searched_addresses = 0  # Initialize a counter to track the number of addresses searched
    
    while True:
        try:
            # Increment the search count each time the loop runs
            searched_addresses += 1
            
            # Generate and print a private key
            private_key = generate_btc_private_key()
            
            # Convert the hexadecimal private key to bytes
            private_key_bytes = bytes.fromhex(private_key)
            
            # Generate public key from private key bytes
            public_key = private_key_to_public_key(private_key_bytes)
            
            legacy_c = legacy_compressed_address(public_key)
            legacy_u = legacy_uncompressed_address(public_key)
            segwit = segwit_address(public_key)
            #taproot = taproot_address(public_key)
            
            addresses = {
                'Legacy (Uncompressed)': legacy_u,
                'Legacy (Compressed)': legacy_c,
                'Segwit': segwit,
            }
            
            print(f"\nScanning: {searched_addresses}")
            print("Private Key (Hex):", private_key)
            print("Legacy (Compressed):", legacy_c)
            print("Legacy (Uncompressed):", legacy_u)
            print("Segwit:", segwit)
            
            balances = check_and_save_balance(addresses, private_key_bytes, private_key_to_wif)
            for addr_type, balance in balances.items():
                print(f"{addr_type} Balance: {balance}")
            
            #time.sleep(1)
        except Exception as e:
            print(f"Error in scan: {e}")
            time.sleep(5)

# Start the continuous scanning
continuous_scan()
