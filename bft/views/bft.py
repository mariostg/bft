from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView
import django.http
from bft.conf import PERIODS, QUARTERS
from bft.forms import BftStatusForm
from bft.models import BftStatus


class HomeView(TemplateView):
    template_name = "bft/bft.html"


def bft_status(request):
    """View that displays the BFT (Business Forecasating Tool) status page.

    This view retrieves the current BFT status and renders it with fiscal year,
    quarter and period information.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: A rendered response containing the BFT status template with
        context including:
            - fy: Current fiscal year
            - quarter: Current quarter description
            - period: Current period description
            - url_name: Name of the URL pattern
            - title: Page title

    Helper Functions:
        get_safe_value: Safely retrieves a value from a mapping with optional offset
    """
    url_name = "bft-status"
    status = BftStatus.current

    def get_safe_value(mapping, key, offset=0):
        try:
            return mapping[int(key) - offset][1] if key is not None else None
        except (TypeError, IndexError):
            return None

    context = {
        "fy": status.fy(),
        "quarter": get_safe_value(QUARTERS, status.quarter()),
        "period": get_safe_value(PERIODS, status.period(), offset=1),
        "url_name": url_name,
        "title": "BFT Status",
    }

    return render(request, f"bft/{url_name}.html", context)


def get_status_json(request):
    """Returns current BFT status as JSON.

    Args:
        request: The HTTP request object.

    Returns:
        JsonResponse: Contains fiscal year, period and quarter information
    """
    status = BftStatus.current
    data = {
        "FY": status.fy(),
        "period": status.period(),
        "quarter": status.quarter(),
    }
    return JsonResponse(data)


def _bft_status_update(request, status: str) -> django.http.HttpResponse:
    """Update BFT status value.

    Args:
        request: The HTTP request object
        status: Status type to update (FY, QUARTER, or PERIOD)

    Returns:
        HttpResponse: Redirects to status page on success or renders form with errors
    """
    try:
        data = BftStatus.objects.get_or_create(status=status, defaults={"value": None})[0]
    except Exception as e:
        messages.error(request, f"Database error: {str(e)}")
        return redirect("bft-status")

    if request.method == "POST":
        form = BftStatusForm(request.POST, instance=data)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"{status} updated successfully")
                return redirect("bft-status")
            except ValueError as err:
                messages.warning(request, f"Invalid value: {err}")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = BftStatusForm(instance=data)

    template = f"bft/{status.lower()}-form.html"
    return render(request, template, {"form": form, "status_type": status})


def bft_fy_update(request):
    return _bft_status_update(request, "FY")


def bft_quarter_update(request):
    return _bft_status_update(request, "QUARTER")


def bft_period_update(request):
    return _bft_status_update(request, "PERIOD")
