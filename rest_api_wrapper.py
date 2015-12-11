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

    def get_content(self, url, **params):
        return self._get(url, params=params).content

    def get_json(self, url="", **params):
        return self._get(url + "/api/json", params=params).json()

    def post(self, url, payload=None, headers=None, **params):
        response = self.session.post(self.direct_uri + url, headers=headers, data=payload, allow_redirects=False, params=params)
        return self._check_response(response, (200, 201))

    def headers(self):
        return self._check_response(self.session.head(self.direct_uri)).headers


class RestkitRestApi(object):
    def __init__(self, direct_uri, username, password, **kwargs):
        super(RestkitRestApi, self).__init__()

        import restkit
        self.restkit = restkit
        import json
        self.json = json

        if username or password:
            filters = kwargs.get('filters', [])
            filters.append(restkit.BasicAuth(username, password))
            kwargs['filters'] = filters

        self.session = restkit.Resource(uri=direct_uri, **kwargs)

    def get_content(self, url, **params):
        try:
            return self.session.get(url, **params).body_string()
        except self.restkit.errors.ResourceNotFound as ex:
            raise ResourceNotFound(str(ex))

    def get_json(self, path="", headers=None, params_dict=None, **params):
        try:
            response = self.session.get(path=path + "/api/json", headers=headers, params_dict=params_dict, **params)
            return self.json.loads(response.body_string())
        except self.restkit.errors.ResourceNotFound as ex:
            raise ResourceNotFound(str(ex))

    def post(self, url, payload=None, headers=None, **params):
        try:
            return self.session.post(url, headers=headers, payload=payload, **params)
        except self.restkit.errors.ResourceNotFound as ex:
            raise ResourceNotFound(str(ex))

    def headers(self):
        try:
            return self.session.head().headers
        except self.restkit.errors.ResourceNotFound as ex:
            raise ResourceNotFound(str(ex))
