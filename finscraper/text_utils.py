"""Module for text processing utility functions and classes."""


def strip_join(text_list, join_with=' '):
    joined_text = join_with.join(text.strip() for text in text_list
                                 if text is not None)
    return joined_text


def paragraph_join(text_list):
    return '\n\n'.join([replace(text, '\n', ' ')
                        for text in strip_elements(text_list)])


def replace(text, source, target):
    return text.replace(source, target) if text is not None else None


def strip_elements(text_list):
    return [text.strip() for text in text_list if text is not None]


def drop_empty_elements(text_list):
    return [text for text in text_list
            if text is not None and (type(text) == str and text.strip() != '')]


def safe_cast_int(text):
    try:
        return int(text)
    except Exception:
        return None
