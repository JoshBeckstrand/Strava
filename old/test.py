import requests

ACCESS_TOKEN = "a9addfbe47897e5a59830b4d379ad35b5e6de626"

res = requests.get(
    "https://www.strava.com/api/v3/athlete",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
)

print(res.status_code)
print(res.json())



69deada47f79d3928120bd6125c5bd1798f781cd = auth code

ce69b6d09cf70c20b42c667d8fce31d1b7d5da5b = refresh 

413f27d03a272177e3e6a4db9eb365ab887ba03b = access 