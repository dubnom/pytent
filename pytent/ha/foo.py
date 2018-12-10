import requests
import json

url = 'http://tentalux.dubno.com/controlsome'
data=[{'number':0, 'brightness':105}]
print(json.dumps(data))

response = requests.post(url, data={'data':json.dumps(data)})
data = response.json()
ARBs = data['ARBs']
arms = len(ARBs)
brightness = sum( [arb[2] for arb in ARBs] ) / arms

print(arms)
print(brightness)
print(data)
