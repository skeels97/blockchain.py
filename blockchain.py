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

        