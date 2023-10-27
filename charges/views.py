from django.shortcuts import render, redirect
from charges.forms import ChargeUploadForm
from charges.models import CostCenterChargeProcessor
from django.contrib import messages


def save_uploaded_file(f):
    with open("drmis_charges.txt", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def process_charges(fy, period):
    cp = CostCenterChargeProcessor()
    monthly_lines = 0

    try:
        cp.to_csv("drmis_charges.txt", period)
    except ValueError as ve:
        return {"error": ve}
    cp.csv2cost_center_charge_import_table(fy, period)
    monthly_lines = cp.monthly_charges(fy, period)


def cost_center_charge_upload(request):
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
                initial = {"fy": fy, period: "ww"}
                form = ChargeUploadForm
            else:
                return redirect("/")
        else:
            print("MMMMMMM")
    else:
        form = ChargeUploadForm
    return render(request, "charges/charges-cc-upload-form.html", {"form": form})
