from django.utils.html import format_html

def colored_status(obj):
    """Return colored HTML based on room status."""
    color_map = {
        'available': '#22c55e',   # Tailwind green-500
        'reserved': '#ef4444',    # Tailwind red-500
        'maintenance': '#f59e0b', # Tailwind amber-500
    }
    color = color_map.get(obj.status, '#6b7280')
    return format_html(
        '<span style="background-color:{}; color:white; padding:2px 8px; border-radius:8px; font-size:0.85em;">{}</span>',
        color,
        obj.get_status_display()
    )