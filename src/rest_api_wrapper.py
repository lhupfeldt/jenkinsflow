import os.path

import requests

from .api_base import AuthError, ClientError


def _join_url(start, end):
    return os.path.join(start.rstrip('/'), end.lstrip('/'))


class ResourceNotFound(Exception):
    pass


class RequestsRestApi():
    def __init__(self, direct_uri, username, password):
        super().__init__()
        self.session = requests.Session()
        if username or password:
            self.session.auth = requests.auth.HTTPBasicAuth(username, password.encode("utf-8"))
        self.direct_uri = direct_uri

    @staticmethod
    def _check_response(response, good_responses=(200,)):
        if response.status_code in good_responses:
            return response

        try:
            response.raise_for_status()
        except Exception as ex:
            if response.status_code == 404:
                raise ResourceNotFound(ex) from ex
            if response.status_code == 401:
                raise AuthError(ex) from ex
            if response.status_code == 403:
                raise ClientError(ex) from ex
            if response.status_code == 500:
                # TODO: Workaround for https://issues.jenkins.io/browse/JENKINS-63845
                # 500 Server Error: Server Error for url: http://localhost:8080/queue/cancelItem?id=14406
                if "Server Error for url:" in str(ex) and "queue/cancelItem" in str(ex):
                    raise ResourceNotFound(ex) from ex
            raise

        # TODO: This is dubious, maybe we should raise here instead.
        return response

    def _get(self, url, params):
        try:
            return self._check_response(self.session.get(_join_url(self.direct_uri, url), params=params))
        except requests.ConnectionError as ex:
            raise ConnectionError(ex) from ex

    def get_content(self, url, **params):
        return self._get(url, params=params).content

    def get_json(self, url="", **params):
        return self._get(_join_url(url, "api/json"), params=params).json()

    def post(self, url, payload=None, headers=None, allow_redirects=False, **params):
        response = self.session.post(_join_url(self.direct_uri, url), headers=headers, data=payload, allow_redirects=allow_redirects, params=params)
        return self._check_response(response, (200, 201))

    def headers(self, allow_redirects=True):
        return self._check_response(self.session.head(self.direct_uri, allow_redirects=allow_redirects)).headers
