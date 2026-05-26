from datetime import timedelta

from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def duration(value):
    if not isinstance(value, timedelta):
        return value
    return str(timedelta(seconds=int(value.total_seconds())))


@register.filter
def kbps(value):
    if value is None:
        return None
    return f'{value // 1000} kbps'


@register.filter
def khz(value):
    if value is None:
        return None
    return f'{value / 1000:g} kHz'


@register.filter
def channels_label(value):
    if value is None:
        return None
    return {1: _('Mono'), 2: _('Stereo')}.get(value, str(value))
