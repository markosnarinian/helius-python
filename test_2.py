from pprint import pprint
from helius.client import HeliusClient

helius = HeliusClient()
response = helius.get_block_production()
pprint(response)
