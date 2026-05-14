from pprint import pprint
import httpx
from dotenv import dotenv_values

config = dotenv_values()
HELIUS_API_KEY = config["HELIUS_API_KEY"]

data = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getSignaturesForAddress",
    "params": ["Ac4ytDhtmrWwA7d8tucsnKEWHo8SPjPKFNGGNA62YUXq"],
}
response = httpx.post(
    f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
    json=data,
)
pprint(response.json())

"""
Sample transaction:
{
    "blockTime": 1778770334,
    "confirmationStatus": "finalized",
    "err": None,
    "memo": None,
    "signature": "37uUTy5baF4wBdUSUshpWcRJUA354gYad6EYS6EN26cg3zJL8pcLJp1Bhsa195esu4HLVA6vTrSjnbNyVnhYHZpm",
    "slot": 419708402,
},
"""
