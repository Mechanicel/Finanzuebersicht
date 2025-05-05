def flip_dict_of_dicts(d: dict) -> dict:
    result = {}
    for outer_k, inner in d.items():
        if not isinstance(inner, dict):
            continue
        for inner_k, val in inner.items():
            result.setdefault(inner_k, {})[outer_k] = val
    return result
