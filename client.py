import requests
import json

API_ENDPOINT = "http://localhost:8080/"

data = {'firstname':'Elon',
        'lastname':'Musk',
        'age':48
				}

if __name__ == '__main__':
	resp = requests.post(url = API_ENDPOINT, data = json.dumps(data))
	print("Response: %s" % resp.text)