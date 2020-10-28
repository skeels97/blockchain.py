import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

class Blockchain(object):

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # creating the genesis block
        self.new_block(previous_hash= '1', proof = 100)

    def register_node(self, address):

        # adds a new node to the list of nodes

        parsed_url = urlparse(address)

        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)   ## types of parsed urls
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        
        else:
            raise ValueError('Invalid URL')


    def valid_chain(self, chain):

        # check if the given blockchain is valid

        last_block = chain[0]   # starts from the genesis block
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n ------------ \n")

            # Check that the hash function of the current block is correct
            if block['previous_hash'] != last_block_hash:
                return False

            # Check if the Proof of Work of the current block is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

            # will keep looping until the whole blockchain has been checked for PoW and correct hash function

        return True


    def resolve_conflicts(self):

        # Consensus algorith; resolves conflicts when they arrise by replacing our blockchain with the longest one present
        # in the network. Hence, everyone will always have the longest valid blockchain saved.

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain) # only look for chains longer than our current one

        # Grab the blockchain and verify across all the nodes in the network

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200: # 200 code = site found
                length = response.json()['length']
                chain = response.json()['chain']

                # check if the length of this blockchain is longer and is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    max_chain = chain


        # Replace our chain if we successfully discovered a new one, valid the chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):

        # Create a new Block in the Blockchain

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or slef.hash(self.chain[-1]),

        }

        # Reset the current list of transactions since they have all already been recorded in the new block above

        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        
        # create a new transaction to go into the next mined block

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):

        # Create a SHA-256 hash of the block

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    
    def proof_of_work(self, last_block):        ##### 

        # A simple version of the Proof of Work Algorith:
        # find a number p' such that hash(pp') contains leading 4 zeroes
        # - where p is the previous proof, and p'is the new proof

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    
    @staticmethod
    def valid_proof(last_proof, proof, last_hash):

        # Validates the proof

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256.hexdigest()
        return guess_hash[:4] == "0000"     ## <<< for the def POW algorith



# Instantiate the Node

app = Flask(__name__)

# Generate a globally unique address for this node

node_identifier = str(uuid4()).replace('-','')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods = ['GET'])
def mine():
    
    # Run the proof of work algorith to get the next proof

    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signifiy that this node has mined a new coin

    blockchain.new_transaction(
        sender = "0"
        recipient = node_identifier,            ##### Invalid Syntax here!!
        amount = 1,

    )

    # Forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response ={
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_trasaction(values['sender'], values['recipient'],values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods = ['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods = ['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)


    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),

    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods = ['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    
    else: 
        response = {
            'message': 'Our chain is authoritative',
            'chain': blochain.chain
        }
    
    return jsonify(response), 200

if __name__ == '__main__':
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type= int, help = 'port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)

        
