import requests
from functools import partial
from const import API_KEY, TEST_HOST
class GsmApi:
    def __init__(self, server_host, api_key) -> None:
        self.api_key = api_key
        self.middleware_server = server_host
        self.headers = {API_KEY: self.api_key}
        self.GET_SERVER_DATA = partial(
            requests.get,
            self.middleware_server,
            headers=self.headers
        )

    #async 
    def get_json_data(self):
        json = self.GET_SERVER_DATA().json()
        return json
        

if __name__ == '__main__':
    api = GsmApi(TEST_HOST,'apitest')
    print(api.get_json_data())