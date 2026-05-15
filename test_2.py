from pprint import pprint
from helius.client import HeliusClient

client = HeliusClient()
response = client.get_signatures_for_address(
    "Ac4ytDhtmrWwA7d8tucsnKEWHo8SPjPKFNGGNA62YUXq"
)
for trasnaction_signature in response:
    print(trasnaction_signature.signature)
    print(trasnaction_signature.slot)
    print(trasnaction_signature.err)
    print(trasnaction_signature.memo)
    print(trasnaction_signature.blockTime)
    print(trasnaction_signature.confirmationStatus)
