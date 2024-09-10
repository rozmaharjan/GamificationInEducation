from django import template

register = template.Library()

@register.filter
def get_item(user_answers, question_id):
    return user_answers.filter(question_id=question_id).first()
