from pprint import pprint
from helius.client import HeliusClient

helius = HeliusClient()
response = helius.get_signatures_for_address("11111111111111111111111111111111")
pprint(response)
