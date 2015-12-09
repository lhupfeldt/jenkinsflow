class ResourceNotFound(Exception):
    pass


class RequestsRestApi(object):
    def __init__(self, direct_uri, username, password):
        super(RequestsRestApi, self).__init__()
        import requests
        self.session = requests.Session()
        if username or password:
            self.session.auth = requests.auth.HTTPBasicAuth(username, password)
        self.direct_uri = direct_uri

    @staticmethod
    def _check_response(response, good_responses=(200,)):
        if response.status_code in good_responses:
            return response
        if response.status_code == 404:
            raise ResourceNotFound(response.request.url)
        response.raise_for_status()

    def _get(self, url, params):
        return self._check_response(self.session.get(self.direct_uri + url, params=params))

    def get(self, url, **params):
        return self._get(url, params=params)

    def get_json(self, url="", **params):
        return self._get(url + "/api/json", params=params).json()

    def post(self, url, payload=None, headers=None, **params):
        response = self.session.post(self.direct_uri + url, headers=headers, data=payload, allow_redirects=False, params=params)
        return self._check_response(response, (200, 201))

    def head(self):
        return self._check_response(self.session.head(self.direct_uri))
