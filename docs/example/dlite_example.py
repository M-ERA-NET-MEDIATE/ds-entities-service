from __future__ import annotations

import requests
from dlite import Instance


def get_instance(uri: str) -> Instance:
    uri = uri.replace("http://onto-ns.com/meta", "http://localhost:8000")
    response = requests.get(uri)
    if not response.ok:
        error_message = (
            f"Could not retrieve instance {uri!r}.\nResponse:\n{response.content}"
        )
        raise RuntimeError(error_message)

    entity = response.json()
    return Instance.from_dict(entity, check_storages=False)
