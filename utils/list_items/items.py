from django.utils.html import format_html


def display_list_items(obj):
    """Pretty-print JSON list of ordered service items."""
    try:
        if isinstance(obj.items, list):
            html = "<ul style='margin:0; padding-left:20px;'>"
            for i in obj.items:

                html += f"<li><b>ID:</b> {i.get('serviceitem_id')} | <b>Qty:</b> {i.get('qty')} | <b>Price:</b> ₹{i.get('price')}</li>"
            html += "</ul>"
            return format_html(html)
        return str(obj.items)
    except Exception as e:
        return f"Invalid data: {e}"
