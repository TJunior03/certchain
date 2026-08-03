from django import template

register = template.Library()


@register.filter
def truncate_hash(value, visible=8):
    text = '' if value is None else str(value).strip()
    if not text:
        return 'Not available'

    if len(text) <= visible * 2 + 3:
        return text

    return f"{text[:visible]}...{text[-visible:]}"
