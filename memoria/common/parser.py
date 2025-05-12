from typing import cast

import orjson
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDict
from ninja.parser import Parser
from ninja.types import DictStrAny


class OrjsonParser(Parser):
    def parse_body(self, request: HttpRequest) -> DictStrAny:
        return cast("DictStrAny", orjson.loads(request.body))

    def parse_querydict(
        self,
        data: MultiValueDict,  # type:ignore[type-arg]
        list_fields: list[str],
        _: HttpRequest,
    ) -> DictStrAny:
        result: DictStrAny = {}
        for key in data:
            if key in list_fields:  # pragma: no cover
                result[key] = data.getlist(key)
            else:
                result[key] = data[key]
        return result
