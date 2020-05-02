"""Module for utility functions."""


def strip_join(text_list):
    joined_text = ' '.join(text.strip() for text in text_list
                           if text is not None)
    return joined_text
