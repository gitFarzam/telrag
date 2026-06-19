from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter(name='convert_markdown')
def convert_markdown(value):
	"""
	This template tag is used for showing markdown properly in the conversations
	"""
	if value is None:
		return ''
	
	# Convert markdown to HTML and mark it as safe
	html = markdown.markdown(
	value,
	extensions=['fenced_code', 'codehilite', 'tables', 'toc']
	)
	
	return mark_safe(html)