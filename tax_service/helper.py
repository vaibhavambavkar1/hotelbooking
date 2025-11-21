from decimal import Decimal
from .models import Tax

def get_gst_taxes(category):
    tax_obj=Tax.objects.get(category=category, active=True)
    if tax_obj:
        return tax_obj.percentage
    else:
        return Decimal("1")


# def get_food_taxes():
#     return Tax.objects.filter(category="food", active=True)
#
# def get_service_taxes():
#     return Tax.objects.filter(category="service", active=True)

def calculate_tax(category,amount):
    total = Decimal("0.00")
    tax_percentage= get_gst_taxes(category)
    total += amount * tax_percentage / Decimal("100")
    return total
