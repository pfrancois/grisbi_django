from django import template

register = template.Library()


class MessagesNode(template.Node):

    def __init__(self, messages):
        self.messages = messages
        super(MessagesNode, self).__init__()

    def render(self, context):
        try:
            messages = context[self.messages]
            tag_prec = ""
            out_str = u''
            for m in messages:
                # Add message
                if tag_prec != "" and m.tags != tag_prec:  # ca veut dire que ce n'est pas le premier tag
                    out_str += u'</ul>\n</div>\n'
                if m.tags != tag_prec:
                    out_str += u'<div class="messages %s">\n<ul class="messages-list-%s">' % (m.tags, m.tags)
                    tag_prec = m.tags
                out_str += u'<li>%s</li>' % m
            out_str += u'</ul>\n</div>\n'
            return out_str
        except KeyError:
            return ''


@register.tag(name='render_messages')
def render_messages(parser, token):
    parts = token.split_contents()
    if len(parts) != 2:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    return MessagesNode(parts[1])
