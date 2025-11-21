from django.utils.html import format_html


def image_view(obj):
    if obj.image:
        return format_html('<img src="{}" width="100" height="70"/>', obj.image.url)
    return "No Image"

def id_image_view(obj):
    if obj.id_proof:
        return format_html('<img src="{}" width="100" height="70"/>', obj.id_proof.url)
    return "No Image"