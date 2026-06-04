from typing import Any

from pydantic import BaseModel


class JsonRpcRequest:
    class Request(BaseModel):
        jsonrpc: str
        method: str
        params: list[Any] | None = None
        id: str | int | None

    def __init__(
        self,
        *,
        jsonrpc: str = "2.0",
        method: str,
        id: str | int | None = 1,
    ):
        self._jsonrpc = jsonrpc
        self._method = method
        self._id = id
        self._positional: list[Any] = []
        self._config: dict[str, Any] = {}

    def add(self, value, can_be_none: bool = False):
        # If dict (for example) strip none values to remove the building burden from the function that calls it
        if value is not None:
            self._positional.append(value)
        elif can_be_none:
            self._positional.append(None)
        return self

    def set(self, key: str, value, can_be_none: bool = False):
        if value is not None:
            self._config.update({key: value})
        elif can_be_none:
            self._config.update({key: None})
        return self

    def build(self):
        params = self._positional if self._positional else []
        if self._config:
            params.append(self._config)
        request = {
            "jsonrpc": self._jsonrpc,
            "method": self._method,
            "id": self._id,
        }
        if params:
            request.update({"params": params})
        return self.Request(**request).model_dump()
