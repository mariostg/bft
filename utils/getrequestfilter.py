def set_query_string(**kwargs) -> str:
    query_string = ""
    query_terms = set()
    for item in kwargs:
        query_terms.add(f"{item}={kwargs[item]}")
    if len(query_terms) > 0:
        query_string = "&".join(query_terms)
    return query_string
