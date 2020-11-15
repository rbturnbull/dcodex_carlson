from django import template
import logging

register = template.Library()

@register.simple_tag
def witness_attests_reading(witness, sublocation, code, parallel):
    return witness.attests_reading(sublocation, code, parallel)
