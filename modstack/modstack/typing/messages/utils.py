from typing import Union

def merge_content(
    first_content: Union[str, list[Union[str, dict]]],
    second_content: Union[str, list[Union[str, dict]]]
) -> Union[str, list[Union[str, dict]]]:
    if isinstance(first_content, str):
        if isinstance(second_content, str):
            return first_content + second_content
        return [first_content] + second_content
    elif isinstance(first_content, list):
        return first_content + second_content
    if isinstance(first_content[-1], str):
        return first_content[:-1] + [first_content[-1] + second_content]
    return [first_content] + second_content