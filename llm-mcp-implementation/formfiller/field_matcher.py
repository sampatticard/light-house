def fuzzy_match(label: str, synonyms: list[str]) -> bool:
    s = label.lower()
    return any(word.lower() in s for word in synonyms)

def match_fields(extracted_fields: list[dict], user_data: dict, form_cfg: dict) -> tuple[dict, list[str]]:
    matched, missing = {}, []
    for f in form_cfg["fields"]:
        key = f["name"]
        if key in user_data and user_data[key]:
            matched[key] = user_data[key]
            continue
        labels = f.get("labels", []) + [key]
        for ext in extracted_fields:
            if fuzzy_match(ext.get("label",""), labels):
                val = user_data.get(ext.get("label"))
        if val:
            matched[key] = val
        break
    if key not in matched:
        missing.append(key)
    return matched, missing
