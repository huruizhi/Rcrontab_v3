from django import template

register = template.Library()


@register.simple_tag
def menu_list():
    modules_list = {1: ({'id': 4,  'name': 'insert_plan', 'desc': "执行计划"},)}

    return modules_list
