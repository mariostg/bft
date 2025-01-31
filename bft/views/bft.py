from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView

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


def ajax_status_request(request):
    status = BftStatus.current
    fy = status.fy()
    # Data
    d = {"Fy": fy, "period": status.period(), "quarter": status.quarter()}
    return JsonResponse(d)


def _bft_status_update(request, status):
    try:
        data = BftStatus.objects.get(status=status)
    except BftStatus.DoesNotExist:
        data = BftStatus(status=status, value=None)
    form = BftStatusForm(instance=data)

    if request.method == "POST":
        form = BftStatusForm(request.POST, instance=data)
        if form.is_valid():
            try:
                form.save()
                return redirect("bft-status")
            except ValueError as err:
                messages.warning(request, err)
                return render(
                    request, f"bft/{status.lower()}-form.html", {"form": form}
                )
    return render(request, f"bft/{status.lower()}-form.html", {"form": form})


def bft_fy_update(request):
    return _bft_status_update(request, "FY")


def bft_quarter_update(request):
    return _bft_status_update(request, "QUARTER")


def bft_period_update(request):
    return _bft_status_update(request, "PERIOD")
