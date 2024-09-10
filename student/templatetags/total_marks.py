from django import template

register = template.Library()

@register.filter
def total_marks(subjects):
    total = 0
    for subject in subjects:
        if hasattr(subject, 'marks_obtained') and isinstance(subject.marks_obtained, (int, float)):
            total += subject.marks_obtained
        else:
            print(f"Warning: subject {subject} does not have a valid marks_obtained attribute")
    return total
