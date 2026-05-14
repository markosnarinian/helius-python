from pprint import pprint
from helius.client import HeliusClient

client = HeliusClient()
response = client.get_signatures_for_address(
    "Ac4ytDhtmrWwA7d8tucsnKEWHo8SPjPKFNGGNA62YUXq"
)
pprint(response)
