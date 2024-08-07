from django.contrib import messages
from django.http import HttpRequest, QueryDict
from django.shortcuts import redirect, render

from bft.forms import ChargeUploadForm
from bft.models import CostCenterChargeProcessor
from main.settings import UPLOADS


def save_uploaded_file(f: QueryDict):
    """Save a DRMIS charges against cost center file in UPLOAD folder.

    Args:
        f (QueryDict): _description_
    """
    with open(f"{UPLOADS}/drmis_charges.txt", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def process_charges(fy, period):
    """Transforms cost center charges text file into a csv file and insert the csv data in cost_center_charge_import table.

    Args:
        fy (int): Fiscal Year the data apply to.
        period (int): Period the data apply to.

    Returns:
        dict: Any error anf number of lines inserted.
    """
    cp = CostCenterChargeProcessor()
    monthly_lines = 0

    try:
        cp.to_csv(f"{UPLOADS}/drmis_charges.txt", period)
    except ValueError as ve:
        return {"error": ve}
    cp.csv2cost_center_charge_import_table(fy, period)
    monthly_lines = cp.monthly_charges(fy, period)
    return {"error": "", "lines": monthly_lines}


def cost_center_charge_upload(request: "HttpRequest"):
    """Process the valid request by saving the report text file, and insert the data in the database.

    Args:
        request (HttpRequest): _description_

    Returns:
        _type_: _description_
    """
    if request.method == "POST":
        form = ChargeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            fy = data["fy"]
            period = data["period"]
            save_uploaded_file(request.FILES["source_file"])
            result = process_charges(fy, period)
            error = result.get("error")
            if error:
                messages.error(request, error)
                form = ChargeUploadForm
            else:
                return redirect("/")
    else:
        form = ChargeUploadForm
    return render(
        request,
        "charges/charges-cc-upload-form.html",
        {
            "form": form,
            "back": "bft",
            "url_name": "cc_charge_upload",
            "title": "Cost Center Charges Upload",
        },
    )
