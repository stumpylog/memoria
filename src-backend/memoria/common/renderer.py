import orjson
from ninja.renderers import BaseRenderer


class OrjsonRenderer(BaseRenderer):
    media_type = "application/json"

    def render(self, request, data, *, response_status):  # noqa: ARG002
        return orjson.dumps(data)
