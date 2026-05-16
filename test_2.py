from pprint import pprint
from helius.client import HeliusClient

helius = HeliusClient()
response = helius.get_block(430)
print(response)
