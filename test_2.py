from pprint import pprint
from helius.client import HeliusClient

helius = HeliusClient()
response = helius.get_cluster_nodes()
pprint(response)
