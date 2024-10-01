from enum import Enum


class ApiType(Enum):
    JENKINS = 0
    SCRIPT = 1
    MOCK = 2


def str_to_apis(api_option: str) -> list[ApiType]:
    return [ApiType[api.strip().upper()] for api in api_option.split(',')]


def apis_to_str(apis: list[ApiType]) -> str:
    return ','.join([api.name for api in apis])
