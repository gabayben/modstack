def parse_connect_string(connection: str) -> tuple[str, str | None]:
    if '.' in connection:
        split_str = connection.split('.', maxsplit=1)
        return split_str[0], split_str[1]
    return connection, None