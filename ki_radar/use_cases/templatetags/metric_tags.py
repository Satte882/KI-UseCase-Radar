from django import template

from ki_radar.use_cases.metric_presentation import build_metric_set_presentation

register = template.Library()


@register.simple_tag
def metric_set(source):
    return build_metric_set_presentation(source)
