import sys
import os.path

from .api_base import AuthError, ClientError


major_version = sys.version_info.major


def encode(text, encoding):
    if major_version >= 3:
        # TODO: Why is this necessary???
        # On python 2 we need to convert from bytes to unicode, but on python 3 we need the reverse!
        return text.encode("utf-8")
    try:
        # TODO: 'unicode' call was needed when implemented, but now seems to be (randomly) raisig TypeError
        # and not actually needed???
        return unicode(text, encoding, errors='ignore')  # pylint: disable=undefined-variable
    except TypeError:
        pass
    return text


def _join_url(start, end):
    return os.path.join(start.rstrip('/'), end.lstrip('/'))


class ResourceNotFound(Exception):
    pass


if major_version < 3:
    # ConnectionError is builtin in Python 3
    class ConnectionError(Exception):
        pass


class RequestsRestApi(object):
    def __init__(self, direct_uri, username, password):
        super(RequestsRestApi, self).__init__()
        import requests
        self.session = requests.Session()
        if username or password:
            self.session.auth = requests.auth.HTTPBasicAuth(username, encode(password, 'latin-1'))
        self.direct_uri = direct_uri

    @staticmethod
    def _check_response(response, good_responses=(200,)):
        if response.status_code in good_responses:
            return response

        try:
            response.raise_for_status()
        except Exception as ex:
            if response.status_code == 404:
                raise ResourceNotFound(ex)
            if response.status_code == 401:
                raise AuthError(ex)
            if response.status_code == 403:
                raise ClientError(ex)
            raise

        # TODO: This is dubious, maybe we should raise here instead.
        return response

    def _get(self, url, params):
        import requests
        try:
            return self._check_response(self.session.get(_join_url(self.direct_uri, url), params=params))
        except requests.ConnectionError as ex:
            raise ConnectionError(ex)

    def get_content(self, url, **params):
        return self._get(url, params=params).content

    def get_json(self, url="", **params):
        return self._get(_join_url(url, "api/json"), params=params).json()

    def post(self, url, payload=None, headers=None, allow_redirects=False, **params):
        response = self.session.post(_join_url(self.direct_uri, url), headers=headers, data=payload, allow_redirects=allow_redirects, params=params)
        return self._check_response(response, (200, 201))

    def headers(self, allow_redirects=True):
        return self._check_response(self.session.head(self.direct_uri, allow_redirects=allow_redirects)).headers


def _check_restkit_response(func):
    def deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except self.restkit.Unauthorized as ex:
            raise AuthError(ex.response.status + " user: '" + self.username + "' for url: " + ex.response.final_url)
        except self.restkit.errors.ResourceNotFound as ex:
            raise ResourceNotFound(str(ex))

    return deco


class RestkitRestApi(object):
    """Note: This is no longer supported or tested, but may still work."""
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

        self.username = username
        self.session = restkit.Resource(uri=direct_uri, **kwargs)

    @_check_restkit_response
    def get_content(self, url, **params):
        return self.session.get(url, **params).body_string()

    @_check_restkit_response
    def get_json(self, path="", headers=None, params_dict=None, **params):
        response = self.session.get(path=_join_url(path, "api/json"), headers=headers, params_dict=params_dict, **params)
        return self.json.loads(response.body_string())

    @_check_restkit_response
    def post(self, url, payload=None, headers=None, allow_redirects=False, **params):  # pylint: disable=unused-argument
        return self.session.post(url, headers=headers, payload=payload, **params)

    @_check_restkit_response
    def headers(self, allow_redirects=True):  # pylint: disable=unused-argument
        return self.session.head().headers
