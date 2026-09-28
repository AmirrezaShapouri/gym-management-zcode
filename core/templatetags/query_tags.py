from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **updates):
    query = context['request'].GET.copy()
    query.pop('page', None)
    for key, value in updates.items():
        query[key] = value
    return query.urlencode()