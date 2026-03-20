from decimal import Decimal
from .models import Tax

def get_gst_taxes(category):
    try:
        tax_obj = Tax.objects.get(category=category, active=True)
        return tax_obj.percentage
    except Tax.DoesNotExist:
        # Return 0 percentage if tax record is not found to prevent crashing
        return Decimal("0.00")
    except Exception:
        # Fallback for any other unexpected errors
        return Decimal("0.00")


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
