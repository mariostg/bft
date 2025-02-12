from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import RestrictedError
from django.shortcuts import redirect, render

from bft import exceptions
from bft.filters import (CapitalInYearFilter, CapitalNewYearFilter,
                         CapitalProjectFilter, CapitalYearEndFilter,
                         CostCenterAllocationFilter, CostCenterFilter,
                         FundCenterAllocationFilter, FundCenterFilter)
from bft.forms import (CapitalForecastingInYearForm,
                       CapitalForecastingNewYearForm,
                       CapitalForecastingYearEndForm, CapitalProjectForm,
                       CostCenterAllocationForm,
                       CostCenterAllocationUploadForm, CostCenterForm,
                       ForecastadjustmentForm, FundCenterAllocationForm,
                       FundCenterAllocationUploadForm, FundCenterForm,
                       FundForm, SourceForm, UploadForm)
from bft.models import (BftStatusManager, CapitalInYear, CapitalNewYear,
                        CapitalProject, CapitalYearEnd, CostCenter,
                        CostCenterAllocation, CostCenterManager,
                        FinancialStructureManager, ForecastAdjustment, Fund,
                        FundCenter, FundCenterAllocation, FundCenterManager,
                        Source)
from bft.uploadprocessor import (CapitalProjectInYearProcessor,
                                 CapitalProjectNewYearProcessor,
                                 CapitalProjectProcessor,
                                 CapitalProjectYearEndProcessor,
                                 CostCenterAllocationProcessor,
                                 CostCenterProcessor,
                                 FundCenterAllocationProcessor,
                                 FundCenterProcessor, FundProcessor,
                                 SourceProcessor)
from main.settings import UPLOADS
from reports.utils import (CostCenterMonthlyAllocationReport,
                           CostCenterMonthlyForecastAdjustmentReport)


def fund_page(request):
    """Display the fund table view.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with fund data, pagination and sorting
    """
    try:
        # Get all funds sorted by fund code
        data = Fund.objects.all().order_by("fund")

        # Add pagination
        paginator = Paginator(data, 15)  # Show 25 funds per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "data": page_obj,
            "page_obj": page_obj,
            "url_name": "fund-table",
            "title": "Funds",
        }

        return render(request, "costcenter/fund-table.html", context)

    except Exception as e:
        messages.error(request, f"Error loading funds: {str(e)}")
        return redirect("home")


def fund_add(request):
    """Create a new fund.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with form or redirect to fund table
    """
    context = {
        "title": "Create Fund",
        "url_name": "fund-table",
        "form": FundForm() if request.method == "GET" else FundForm(request.POST),
    }

    if request.method == "POST":
        if context["form"].is_valid():
            try:
                # Save the form and normalize fund code to uppercase
                fund: Fund = context["form"].save(commit=False)
                fund.fund = fund.fund.upper()
                if fund.name:
                    fund.name = fund.name.upper()
                fund.save()

                messages.success(request, f"Fund {fund.fund} created successfully")
                return redirect("fund-table")

            except IntegrityError:
                messages.error(request, f"Fund {fund.fund} already exists")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below")

    return render(request, "costcenter/fund-form.html", context)


def fund_update(request, pk):
    """Update an existing fund.

    Args:
        request: The HTTP request object
        pk: Primary key of the fund to update

    Returns:
        Rendered template with form or redirect to fund table
    """
    try:
        fund = Fund.objects.get(id=pk)
    except Fund.DoesNotExist:
        messages.error(request, f"Fund with id {pk} does not exist")
        return redirect("fund-table")

    if request.method == "POST":
        form = FundForm(request.POST, instance=fund)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Fund {fund.fund} updated successfully")
                return redirect("fund-table")
            except IntegrityError:
                messages.error(request, "Fund with this code already exists")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = FundForm(instance=fund)

    context = {
        "form": form,
        "title": "Update Fund",
        "url_name": "fund-table",
    }

    return render(request, "costcenter/fund-form.html", context)


def fund_delete(request, pk):
    fund = Fund.objects.get(id=pk)
    if request.method == "POST":
        try:
            fund.delete()
        except RestrictedError as e:
            msg = e.args[0].split(":")[0] + " : "
            fkeys = []
            for fk in e.restricted_objects:
                fkeys.append(fk.costcenter)
            msg = msg + ", ".join(fkeys)
            messages.warning(request, msg)
        return redirect("fund-table")
    context = {"object": fund, "back": "fund-table"}
    return render(request, "core/delete-object.html", context)


def fund_upload(request):
    url_name = "fund-upload"
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = FundProcessor(filepath, user)
            processor.main(request)
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {"form": form, "title": "Fund Upload", "back": "bft", "url_name": url_name},
    )


def source_page(request):
    """Display the source table view.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with source data, pagination and sorting
    """
    try:
        # Get all sources sorted by source code
        data = Source.objects.all().order_by("source")

        # Add pagination
        paginator = Paginator(data, 15)  # Show 15 sources per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "page_obj": page_obj,
            "url_name": "source-table",
            "title": "Sources",
        }

        return render(request, "costcenter/source-table.html", context)

    except Exception as e:
        messages.error(request, f"Error loading sources: {str(e)}")
        return redirect("home")


def source_add(request):
    """Create a new source.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with form or redirect to source table
    """
    context = {
        "title": "Create Source",
        "url_name": "source-table",
        "form": SourceForm() if request.method == "GET" else SourceForm(request.POST),
    }

    if request.method == "POST":
        if context["form"].is_valid():
            try:
                # Save form and normalize source code to uppercase
                source = context["form"].save(commit=False)
                source.source = source.source.upper()
                source.save()

                messages.success(request, f"Source {source.source} created successfully")
                return redirect("source-table")

            except IntegrityError:
                messages.error(request, f"Source {source.source} already exists")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below")

    return render(request, "costcenter/source-form.html", context)


def source_update(request, pk):
    """Update an existing source.

    Args:
        request: The HTTP request object
        pk: Primary key of the source to update

    Returns:
        Rendered template with form or redirect to source table
    """
    try:
        source = Source.objects.get(id=pk)
    except Source.DoesNotExist:
        messages.error(request, f"Source with id {pk} does not exist")
        return redirect("source-table")

    if request.method == "POST":
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Source {source.source} updated successfully")
                return redirect("source-table")
            except IntegrityError:
                messages.error(request, "Source with this code already exists")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = SourceForm(instance=source)

    context = {
        "form": form,
        "title": "Update Source",
        "url_name": "source-table",
    }

    return render(request, "costcenter/source-form.html", context)


def source_delete(request, pk):
    source = Source.objects.pk(pk)
    if request.method == "POST":
        try:
            source.delete()
        except RestrictedError as e:
            msg = e.args[0].split(":")[0] + " : "
            fkeys = []
            for fk in e.restricted_objects:
                fkeys.append(fk.costcenter)
            msg = msg + ", ".join(fkeys)
            messages.warning(request, msg)
        return redirect("source-table")
    context = {"object": source, "back": "source-table"}
    return render(request, "core/delete-object.html", context)


def source_upload(request):
    url_name = "source-upload"
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = SourceProcessor(filepath, user)
            processor.main(request)
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {"form": form, "title": "Source Upload", "back": "bft", "url_name": url_name},
    )


def fundcenter_page(request):
    """Display the fund center table view with filtering and pagination.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with fund center data, filter, pagination
    """
    has_filter = False
    if not request.GET:
        data = None
    else:
        data = FundCenter.objects.all().order_by("sequence")
        has_filter = True

    search_filter = FundCenterFilter(request.GET, queryset=data)
    paginator = Paginator(search_filter.qs, 25)  # Show 25 items per page
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.get_page(page_number)
    except:
        messages.error(request, "Error loading fund centers")
        return redirect("home")

    return render(
        request,
        "costcenter/fundcenter-table.html",
        {
            "filter": search_filter,
            "page_obj": page_obj,
            "has_filter": has_filter,
            "url_name": "fundcenter-table",
            "title": "Fund Centers",
        },
    )


def fundcenter_add(request):
    """Create a new fund center.

    Args:
        request: HTTP request object

    Returns:
        Rendered template with form or redirect to fund center table
    """
    context = {
        "title": "Create Fund Center",
        "url_name": "fundcenter-table",
        "form": FundCenterForm() if request.method == "GET" else FundCenterForm(request.POST),
    }

    if request.method == "POST":
        if context["form"].is_valid():
            try:
                # Prepare fund center object
                obj = context["form"].save(commit=False)

                # Set sequence using financial structure manager
                fsm = FinancialStructureManager()
                obj.sequence = fsm.set_parent(fundcenter_parent=obj.fundcenter_parent)

                # Normalize codes to uppercase
                obj.fundcenter = obj.fundcenter.upper()
                if obj.shortname:
                    obj.shortname = obj.shortname.upper()

                # Save to database
                obj.save()
                messages.success(request, f"Fund center {obj.fundcenter} created successfully")
                return redirect("fundcenter-table")

            except IntegrityError:
                messages.error(request, f"Fund center {obj.fundcenter} already exists")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error creating fund center: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below")

    return render(request, "costcenter/fundcenter-form.html", context)


def fundcenter_update(request, pk):
    """Update an existing fund center.

    Args:
        request: The HTTP request object
        pk: Primary key of the fund center to update

    Returns:
        Rendered template with form or redirect to fund center table
    """
    try:
        # Get fund center or return 404
        fundcenter = FundCenter.objects.get(id=pk)
    except FundCenter.DoesNotExist:
        messages.error(request, f"Fund center with id {pk} does not exist")
        return redirect("fundcenter-table")

    if request.method == "POST":
        form = FundCenterForm(request.POST, instance=fundcenter)
        if form.is_valid():
            obj = form.save(commit=False)

            # Normalize fund center codes to uppercase
            obj.fundcenter = obj.fundcenter.upper()
            if obj.shortname:
                obj.shortname = obj.shortname.upper()

            # Check if parent changed and update sequence if needed
            current = FundCenterManager().pk(obj.pk)
            if obj.fundcenter_parent != current.fundcenter_parent:
                fsm = FinancialStructureManager()
                try:
                    obj.sequence = fsm.set_parent(fundcenter_parent=obj.fundcenter_parent)
                except Exception as e:
                    messages.error(request, f"Error updating parent sequence: {str(e)}")
                    return render(
                        request,
                        "costcenter/fundcenter-form.html",
                        {"form": form, "url_name": "fundcenter-table", "title": "Fund Center Update"},
                    )

            try:
                obj.save()
                messages.success(request, f"Fund center {obj.fundcenter} updated successfully")
                return redirect("fundcenter-table")
            except IntegrityError:
                messages.error(request, "A fund center with this code already exists")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = FundCenterForm(instance=fundcenter)

    context = {
        "form": form,
        "url_name": "fundcenter-table",
        "title": "Fund Center Update",
    }
    return render(request, "costcenter/fundcenter-form.html", context)


def fundcenter_delete(request, pk):
    fundcenter = FundCenter.objects.get(id=pk)
    if request.method == "POST":
        try:
            fundcenter.delete()
        except RestrictedError as e:
            msg = e.args[0].split(":")[0] + " : "
            fkeys = []
            for fk in e.restricted_objects:
                if isinstance(fk, CapitalProject):
                    fkeys.append(fk.project_no)
                elif isinstance(fk, FundCenter):
                    fkeys.append(fk.fundcenter)
                elif isinstance(fk, CostCenter):
                    fkeys.append(fk.costcenter)
            msg = msg + ", ".join(fkeys)
            messages.warning(request, msg)
        return redirect("fundcenter-table")
    context = {"object": fundcenter, "back": "fundcenter-table"}
    return render(request, "core/delete-object.html", context)


def fundcenter_upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/fundcenter-upload-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = FundCenterProcessor(filepath, user)
            processor.main(request)
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {"form": form, "title": "Fund Center Upload", "back": "bft"},
    )


def fundcenter_allocation_page(request):
    if not request.GET:
        data = FundCenterAllocation.objects.none()
    else:
        data = FundCenterAllocation.objects.all().order_by("fundcenter")
    search_filter = FundCenterAllocationFilter(request.GET, queryset=data)
    return render(
        request,
        "costcenter/fundcenter-allocation-table.html",
        {
            "filter": search_filter,
            "url_name": "fundcenter-allocation-table",
            "title": "Fund Centers Allocation Table",
        },
    )


def fundcenter_allocation_add(request):
    context = {
        "title": "Fund Center Allocation Create",
        "url_name": "fundcenter-allocation-table",
    }
    if request.method == "POST":
        form = FundCenterAllocationForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.user = request.user
            form.save()
            return redirect("fundcenter-allocation-table")
        else:
            err = form.errors.get_json_data()["__all__"][0]["message"]
            messages.warning(request, err)
    else:
        context["form"] = FundCenterAllocationForm

    return render(
        request,
        "costcenter/fundcenter-allocation-form.html",
        context,
    )


def fundcenter_allocation_update(request, pk):
    data = FundCenterAllocation.objects.get(id=pk)
    form = FundCenterAllocationForm(instance=data)
    if request.method == "POST":
        form = FundCenterAllocationForm(request.POST, instance=data)
        if form.is_valid():
            form = form.save(commit=False)
            form.owner = request.user
            form.save()
            return redirect("fundcenter-allocation-table")
        else:
            err = form.errors.get_json_data()["__all__"][0]["message"]
            messages.warning(request, err)
    context = {
        "form": form,
        "title": "Fund Center Allocation Update",
        "url_name": "fundcenter-allocation-table",
    }
    return render(
        request,
        "costcenter/fundcenter-allocation-form.html",
        context,
    )


def fundcenter_allocation_delete(request, pk):
    item = FundCenterAllocation.objects.get(id=pk)
    if request.method == "POST":
        item.delete()
        return redirect("fundcenter-allocation-table")
    context = {"object": item, "back": "fundcenter-allocation-table"}
    return render(request, "core/delete-object.html", context)


def fundcenter_allocation_upload(request):
    """Process the valid request by importing a file containing fund center allocations inside the database.

    Args:
        request (HttpRequest): _description_

    """
    url_name = "fundcenter-allocation-upload"
    if request.method == "POST":
        form = FundCenterAllocationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            fy = data["fy"]
            quarter = data["quarter"]
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            ap = FundCenterAllocationProcessor(filepath, fy, quarter, user)
            ap.main(request)
    else:
        form = FundCenterAllocationUploadForm
    return render(
        request,
        "core/form-upload.html",
        {
            "form": form,
            "title": "Fund Centers Allocation Upload",
            "back": "bft",
            "url_name": url_name,
        },
    )


def capital_project_page(request):
    """Display the capital project table view with filtering and pagination.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with capital project data, filter, pagination
    """
    has_filter = False
    if not request.GET:
        data = None
    else:
        data = CapitalProject.objects.all().order_by("project_no")
        has_filter = True

    search_filter = CapitalProjectFilter(request.GET, queryset=data)
    paginator = Paginator(search_filter.qs, 25)  # Show 25 items per page
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.get_page(page_number)
    except:
        messages.error(request, "Error loading capital projects")
        return redirect("home")

    return render(
        request,
        "costcenter/capitalproject-table.html",
        {
            "filter": search_filter,
            "page_obj": page_obj,
            "has_filter": has_filter,
            "url_name": "capital-project-table",
            "title": "Capital Projects",
        },
    )


def capital_project_add(request):
    """Create a new capital project.

    Args:
        request: HTTP request object

    Returns:
        Rendered template with form or redirect to capital project table
    """
    context = {
        "title": "Create Capital Project",  # More descriptive title
        "url_name": "capital-project-table",
        "form": CapitalProjectForm() if request.method == "GET" else CapitalProjectForm(request.POST),
    }

    if request.method == "POST":
        if context["form"].is_valid():
            try:
                # Prepare capital project object
                obj = context["form"].save(commit=False)

                # Normalize codes to uppercase
                obj.project_no = obj.project_no.upper()
                if obj.shortname:
                    obj.shortname = obj.shortname.upper()

                # Save to database
                obj.save()
                messages.success(request, f"Capital project {obj.project_no} created successfully")
                return redirect("capital-project-table")

            except IntegrityError:
                messages.error(request, f"Capital project {obj.project_no} already exists")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error creating capital project: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below")

    return render(request, "costcenter/capitalproject-form.html", context)


def capital_project_update(request, pk):
    """Update an existing capital project.

    Args:
        request: The HTTP request object
        pk: Primary key of the capital project to update

    Returns:
        Rendered template with form or redirect to project table
    """
    try:
        # Get capital project or return 404
        capital_project = CapitalProject.objects.get(pk=pk)
    except CapitalProject.DoesNotExist:
        messages.error(request, f"Capital project with id {pk} does not exist")
        return redirect("capital-project-table")

    if request.method == "POST":
        form = CapitalProjectForm(request.POST, instance=capital_project)
        if form.is_valid():
            obj = form.save(commit=False)

            # Normalize project number to uppercase
            obj.project_no = obj.project_no.upper()
            if obj.shortname:
                obj.shortname = obj.shortname.upper()

            try:
                obj.save()
                messages.success(request, f"Capital project {obj.project_no} updated successfully")
                return redirect("capital-project-table")
            except IntegrityError:
                messages.error(request, "A capital project with this number already exists")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = CapitalProjectForm(instance=capital_project)

    context = {
        "form": form,
        "title": "Update Capital Project",
        "url_name": "capital-project-table",
    }
    return render(request, "costcenter/capitalproject-form.html", context)


def capital_project_delete(request, pk):
    obj = CapitalProject.objects.get(id=pk)
    if request.method == "POST":
        try:
            obj.delete()
        except RestrictedError:
            messages.warning(
                request,
                f"Cannot delete {obj.project_no} because it contains dependants elements",
            )
        return redirect("capital-project-table")
    context = {"object": obj, "back": "capital-project-table"}
    return render(request, "core/delete-object.html", context)


def capital_project_upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/capital-project-upload-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = CapitalProjectProcessor(filepath, user)
            processor.main(request)
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {"form": form, "title": "Capital Project Upload", "back": "bft", "url_name": "capital-project-upload"},
    )


def capital_forecasting_new_year_table(request):
    has_filter = False
    status = {"fy": BftStatusManager().fy(), "period": BftStatusManager().period}
    if not request.GET:
        data = None
    else:
        data = CapitalNewYear.objects.all()
        has_filter = True
    search_filter = CapitalNewYearFilter(request.GET, queryset=data)
    paginator = Paginator(search_filter.qs, 25)
    page_number = request.GET.get("page")
    return render(
        request,
        "costcenter/capital-forecasting-new-year-table.html",
        {
            "filter": search_filter,
            "data": paginator.get_page(page_number),
            "status": status,
            "has_filter": has_filter,
            "url_name": "capital-forecasting-new-year-table",
            "title": "Capital Forecasting New Year",
        },
    )


def capital_forecasting_new_year_add(request):
    context = {
        "title": "Create Capital Forecasting New Year",
        "url_name": "capital-forecasting-new-year-table",
    }
    if request.method == "POST":
        form = CapitalForecastingNewYearForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.save()
            except IntegrityError as e:
                messages.error(
                    request,
                    f"{e}.  Capital Forecasting {obj.project_no} {obj.fy} {obj.fund} exists",
                )
                return render(
                    request,
                    "costcenter/capital-forecasting-new-year-form.html",
                    context,
                )
            return redirect("capital-forecasting-new-year-table")
    else:
        context["form"] = CapitalForecastingNewYearForm

    return render(
        request,
        "costcenter/capital-forecasting-new-year-form.html",
        context,
    )


def capital_forecasting_new_year_update(request, pk):
    obj = CapitalNewYear.objects.get(pk=pk)
    form = CapitalForecastingNewYearForm(instance=obj)

    if request.method == "POST":
        form = CapitalForecastingNewYearForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "Duplicate entry cannot be saved")
            return redirect("capital-forecasting-new-year-table")
    context = {
        "form": form,
        "url_name": "capital-forecasting-new-year-table",
        "title": "Update Capital Forecasting New Year",
    }
    return render(
        request,
        "costcenter/capital-forecasting-new-year-form.html",
        context,
    )


def capital_forecasting_new_year_delete(request, pk):
    obj = CapitalNewYear.objects.get(id=pk)
    if request.method == "POST":
        obj.delete()
        return redirect("capital-forecasting-new-year-table")
    context = {"object": obj, "back": "capital-forecasting-new-year-table"}
    return render(request, "core/delete-object.html", context)


def capital_forecasting_in_year_table(request):
    has_filter = False
    status = {"fy": BftStatusManager().fy(), "period": BftStatusManager().period}
    if not request.GET:
        data = None
    else:
        data = CapitalInYear.objects.all()
        has_filter = True
    search_filter = CapitalInYearFilter(request.GET, queryset=data)
    paginator = Paginator(search_filter.qs, 25)
    page_number = request.GET.get("page")
    return render(
        request,
        "costcenter/capital-forecasting-in-year-table.html",
        {
            "filter": search_filter,
            "data": paginator.get_page(page_number),
            "status": status,
            "has_filter": has_filter,
            "url_name": "capital-forecasting-in-year-table",
            "title": "Capital Forecasting In Year",
        },
    )


def capital_forecasting_in_year_add(request):
    context = {
        "title": "Create Capital Forecasting In Year",
        "url_name": "capital-forecasting-in-year-table",
    }
    if request.method == "POST":
        form = CapitalForecastingInYearForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.save()
            except IntegrityError as e:
                messages.error(
                    request,
                    f"{e}.  Capital Forecasting {obj.project_no} {obj.fy} {obj.fund} exists",
                )
                return render(
                    request,
                    "costcenter/capital-forecasting-in-year-form.html",
                    {"form": form},
                )
            return redirect("capital-forecasting-in-year-table")
    else:
        context["form"] = CapitalForecastingInYearForm

    return render(
        request,
        "costcenter/capital-forecasting-in-year-form.html",
        context,
    )


def capital_forecasting_in_year_update(request, pk):
    obj = CapitalInYear.objects.get(pk=pk)
    form = CapitalForecastingInYearForm(instance=obj)

    if request.method == "POST":
        form = CapitalForecastingInYearForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "Duplicate entry cannot be saved")
            return redirect("capital-forecasting-in-year-table")
    context = {
        "form": form,
        "title": "Update Capital Forecasting In Year",
        "url_name": "capital-forecasting-in-year-table",
    }
    return render(
        request,
        "costcenter/capital-forecasting-in-year-form.html",
        context,
    )


def capital_forecasting_in_year_delete(request, pk):
    obj = CapitalInYear.objects.get(id=pk)
    if request.method == "POST":
        obj.delete()
        return redirect("capital-forecasting-in-year-table")
    context = {"object": obj, "back": "capital-forecasting-in-year-table"}
    return render(request, "core/delete-object.html", context)


def capital_forecasting_year_end_table(request):
    has_filter = False
    status = {"fy": BftStatusManager().fy(), "period": BftStatusManager().period}
    if not request.GET:
        data = None
    else:
        data = CapitalYearEnd.objects.all()
        has_filter = True
    search_filter = CapitalYearEndFilter(request.GET, queryset=data)
    paginator = Paginator(search_filter.qs, 25)
    page_number = request.GET.get("page")
    return render(
        request,
        "costcenter/capital-forecasting-year-end-table.html",
        {
            "filter": search_filter,
            "data": paginator.get_page(page_number),
            "status": status,
            "has_filter": has_filter,
            "url_name": "capital-forecasting-year-end-table",
            "title": "Capital Forecasting Year End Table",
        },
    )


def capital_forecasting_year_end_add(request):
    context = {
        "title": "Create Capital Forecasting Year End",
        "url_name": "capital-forecasting-year-end-table",
    }
    if request.method == "POST":
        form = CapitalForecastingYearEndForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.save()
            except IntegrityError as e:
                messages.error(
                    request,
                    f"{e}.  Capital Forecasting Year End {obj.project_no} {obj.fy} {obj.fund} exists",
                )
                return render(
                    request,
                    "costcenter/capital-forecasting-year-end-form.html",
                    {"form": form},
                )
            return redirect("capital-forecasting-year-end-table")
    else:
        context["form"] = CapitalForecastingYearEndForm

    return render(request, "costcenter/capital-forecasting-year-end-form.html", context)


def capital_forecasting_year_end_update(request, pk):
    obj = CapitalYearEnd.objects.get(pk=pk)
    form = CapitalForecastingYearEndForm(instance=obj)

    if request.method == "POST":
        form = CapitalForecastingYearEndForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "Duplicate entry cannot be saved")
            return redirect("capital-forecasting-year-end-table")

    context = {
        "form": form,
        "url_name": "capital-forecasting-year-end-table",
        "title": "Update Capital Forecasting Year End",
    }
    return render(
        request,
        "costcenter/capital-forecasting-year-end-form.html",
        context,
    )


def capital_forecasting_year_end_delete(request, pk):
    obj = CapitalYearEnd.objects.get(id=pk)
    if request.method == "POST":
        obj.delete()
        return redirect("capital-forecasting-year-end-table")
    context = {"object": obj, "back": "capital-forecasting-year-end-table"}
    return render(request, "core/delete-object.html", context)


def capital_forecasting_new_year_upload(request):
    url_name = "capital-forecasting-new-year-upload"
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = CapitalProjectNewYearProcessor(filepath, user, request)
            processor.main()
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {
            "form": form,
            "title": "Capital Forecasting New Year Upload",
            "back": "bft",
            "url_name": url_name,
        },
    )


def capital_forecasting_in_year_upload(request):
    url_name = "capital-forecasting-in-year-upload"
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = CapitalProjectInYearProcessor(filepath, user, request)
            processor.main()
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {
            "form": form,
            "title": "Capital Forecasting In Year Upload",
            "back": "bft",
            "url_name": url_name,
        },
    )


def capital_forecasting_year_end_upload(request):
    url_name = "capital-forecasting-year-end-upload"
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = CapitalProjectYearEndProcessor(filepath, user, request)
            processor.main()
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {"form": form, "title": "Capital Project Year End Upload", "back": "bft", "url_name": url_name},
    )


def costcenter_page(request):
    """Display the cost center table view with filtering and pagination.

    Args:
        request: The HTTP request object

    Returns:
        Rendered template with cost center data, filter, pagination
    """
    has_filter = False
    if not request.GET:
        data = None
    else:
        data = CostCenter.objects.all().order_by("costcenter")
        has_filter = True
    search_filter = CostCenterFilter(request.GET, queryset=data)
    paginator = Paginator(search_filter.qs, 5)  # Show 25 items per page
    print(paginator)
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.get_page(page_number)
    except:
        messages.error(request, "Error loading cost centers")
        return redirect("home")

    return render(
        request,
        "costcenter/costcenter-table.html",
        {
            "filter": search_filter,
            "page_obj": page_obj,
            "has_filter": has_filter,
            "url_name": "costcenter-table",
            "title": "Cost Centers",
        },
    )


def costcenter_add(request):
    """Create a new cost center.

    Args:
        request: HTTP request object

    Returns:
        Rendered template with form or redirect to cost center table
    """
    context = {
        "title": "Create Cost Center",
        "url_name": "costcenter-table",
        "form": CostCenterForm() if request.method == "GET" else CostCenterForm(request.POST),
    }

    if request.method == "POST":
        if context["form"].is_valid():
            try:
                # Prepare cost center object
                obj = context["form"].save(commit=False)

                # Set sequence using financial structure manager
                fsm = FinancialStructureManager()
                obj.sequence = fsm.set_parent(fundcenter_parent=obj.costcenter_parent, costcenter_child=True)

                # Normalize codes to uppercase
                obj.costcenter = obj.costcenter.upper()
                if obj.shortname:
                    obj.shortname = obj.shortname.upper()

                # Save to database
                obj.save()
                messages.success(request, f"Cost center {obj.costcenter} created successfully")
                return redirect("costcenter-table")

            except IntegrityError:
                messages.error(request, f"Cost center {obj.costcenter} already exists")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error creating cost center: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below")

    return render(request, "costcenter/costcenter-form.html", context)


def costcenter_update(request, pk):
    """Update an existing cost center.

    Args:
        request: The HTTP request object
        pk: Primary key of the cost center to update

    Returns:
        Rendered template with form or redirect to cost center table
    """
    try:
        # Get cost center or return 404
        costcenter = CostCenter.objects.get(id=pk)
    except CostCenter.DoesNotExist:
        messages.error(request, f"Cost center with id {pk} does not exist")
        return redirect("costcenter-table")

    if request.method == "POST":
        form = CostCenterForm(request.POST, instance=costcenter)
        if form.is_valid():
            obj = form.save(commit=False)

            # Normalize cost center codes to uppercase
            obj.costcenter = obj.costcenter.upper()
            if obj.shortname:
                obj.shortname = obj.shortname.upper()

            # Check if parent changed and update sequence if needed
            current = CostCenterManager().pk(obj.pk)
            if obj.costcenter_parent != current.costcenter_parent:
                fsm = FinancialStructureManager()
                try:
                    obj.sequence = fsm.set_parent(fundcenter_parent=obj.costcenter_parent, costcenter_child=obj)
                except Exception as e:
                    messages.error(request, f"Error updating parent sequence: {str(e)}")
                    return render(
                        request,
                        "costcenter/costcenter-form.html",
                        {"form": form, "url_name": "costcenter-table", "title": "Cost Center Update"},
                    )

            try:
                obj.save()
                messages.success(request, f"Cost center {obj.costcenter} updated successfully")
                return redirect("costcenter-table")
            except IntegrityError:
                messages.error(request, "A cost center with this code already exists")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = CostCenterForm(instance=costcenter)

    context = {
        "form": form,
        "url_name": "costcenter-table",
        "title": "Cost Center Update",
    }
    return render(request, "costcenter/costcenter-form.html", context)


def costcenter_delete(request, pk):
    costcenter = CostCenter.objects.get(id=pk)
    if request.method == "POST":
        try:
            costcenter.delete()
        except RestrictedError:
            messages.warning(
                request,
                f"Cannot delete {costcenter.costcenter} because it contains dependants elements",
            )
        return redirect("costcenter-table")
    context = {"object": costcenter, "back": "costcenter-table"}
    return render(request, "core/delete-object.html", context)


def costcenter_upload(request):
    url_name = "costcenter-upload"
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = CostCenterProcessor(filepath, user)
            processor.main(request)
    else:
        form = UploadForm
    return render(
        request,
        "core/form-upload.html",
        {"form": form, "title": "Cost Center Upload", "back": "bft", "url_name": url_name},
    )


def costcenter_allocation_page(request):
    if not request.GET:
        data = CostCenterAllocation.objects.none()
    else:
        data = CostCenterAllocation.objects.all().order_by("costcenter")
    search_filter = CostCenterAllocationFilter(request.GET, queryset=data)
    return render(
        request,
        "costcenter/costcenter-allocation-table.html",
        {
            "filter": search_filter,
            "url_name": "costcenter-allocation-table",
            "title": "Cost Centers Allocation Table",
        },
    )


def costcenter_allocation_add(request):
    if request.method == "POST":
        form = CostCenterAllocationForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.user = request.user
            form.save()
            c = CostCenterMonthlyAllocationReport(form.fy, BftStatusManager().period(), quarter=form.quarter)
            c.insert_grouped_allocation(c.sum_allocation_cost_center())

            return redirect("costcenter-allocation-table")
        else:
            err = form.errors
            try:
                warning = err.get_json_data()["__all__"][0]["message"]
                messages.warning(request, warning)
            except Exception:
                pass
    else:
        form = CostCenterAllocationForm

    return render(
        request,
        "costcenter/costcenter-allocation-form.html",
        {
            "form": form,
            "title": "Create Cost Center Allocation",
            "url_name": "costcenter-allocation-add",
        },
    )


def costcenter_allocation_update(request, pk):
    data = CostCenterAllocation.objects.get(id=pk)
    form = CostCenterAllocationForm(instance=data)
    if request.method == "POST":
        form = CostCenterAllocationForm(request.POST, instance=data)
        if form.is_valid():
            form = form.save(commit=False)
            form.owner = request.user
            form.save()
            c = CostCenterMonthlyAllocationReport(form.fy, BftStatusManager().period(), quarter=form.quarter)
            c.insert_grouped_allocation(c.sum_allocation_cost_center())
            return redirect("costcenter-allocation-table")
        else:
            err = form.errors.get_json_data()["__all__"][0]["message"]
            messages.warning(request, err)
    return render(request, "costcenter/costcenter-allocation-form.html", {"form": form})


def costcenter_allocation_delete(request, pk):
    item = CostCenterAllocation.objects.get(id=pk)
    if request.method == "POST":
        item.delete()
        c = CostCenterMonthlyAllocationReport(item.fy, BftStatusManager().period(), quarter=item.quarter)
        c.insert_grouped_allocation(c.sum_allocation_cost_center())
        return redirect("costcenter-allocation-table")
    context = {"object": item, "back": "costcenter-allocation-table"}
    return render(request, "core/delete-object.html", context)


def costcenter_allocation_upload(request):
    """Process the valid request by importing a file containing cost center allocations inside the database.

    Args:
        request (HttpRequest): _description_

    """
    url_name = "cost-center-allocation-upload"
    if request.method == "POST":
        form = CostCenterAllocationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            fy = data["fy"]
            quarter = data["quarter"]
            user = request.user
            filepath = f"{UPLOADS}/{url_name}-{user}.txt"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            ap = CostCenterAllocationProcessor(filepath, fy, quarter, user)
            ap.main(request)
    else:
        form = CostCenterAllocationUploadForm
    return render(
        request,
        "core/form-upload.html",
        {
            "form": form,
            "title": "Cost Center Allocation Upload",
            "back": "bft",
            "url_name": url_name,
        },
    )


def forecast_adjustment_page(request):
    data = ForecastAdjustment.objects.all()
    if data.count() == 0:
        messages.info(request, "There are no forecast adjustment.")
    context = {
        "data": data,
        "url_name": "forecast-adjustment-table",
        "title": "Cost Centers Forecast Adjustment Table",
    }
    return render(request, "costcenter/forecast-adjustment-table.html", context)


# @login_required
def forecast_adjustment_add(request):
    """Create a forecast adjustment for the specified cost center and fund.
    The adjustment will be reflected in the monthly data of the current period.
    """
    context = {
        "title": "Create Forecast Adjustment",
        "url_name": "forecast-adjustment-table",
    }
    if request.method == "POST":
        form = ForecastadjustmentForm(request.POST)
        if form.is_valid():
            context["form"] = form
            form = form.save(commit=False)
            form.user = request.user
            try:
                form.save()
                c = CostCenterMonthlyForecastAdjustmentReport(BftStatusManager().fy(), BftStatusManager().period())
                c.insert_grouped_forecast_adjustment(c.sum_forecast_adjustments())
            except exceptions.LineItemsDoNotExistError:
                messages.warning(
                    request, f"Cost center {form.costcenter} has no line items"
                )
            return redirect("forecast-adjustment-table")
    else:
        context["form"] = ForecastadjustmentForm

    return render(
        request,
        "costcenter/forecast-adjustment-form.html",
        context,
    )


# @login_required
def forecast_adjustment_update(request, pk):
    forecastadjustment = ForecastAdjustment.objects.get(id=pk)
    form = ForecastadjustmentForm(instance=forecastadjustment)

    if request.method == "POST":
        form = ForecastadjustmentForm(request.POST, instance=forecastadjustment)
        if form.is_valid():
            form = form.save(commit=False)
            form.owner = request.user
            form.save()
            c = CostCenterMonthlyForecastAdjustmentReport(BftStatusManager().fy(), BftStatusManager().period())
            c.insert_grouped_forecast_adjustment(c.sum_forecast_adjustments())
            return redirect("forecast-adjustment-table")
    context = {
        "form": form,
        "url_name": "forecast-adjustment-table",
        "title": "Update Forecast Adjustment",
    }
    return render(request, "costcenter/forecast-adjustment-form.html", context)


# @login_required
def forecast_adjustment_delete(request, pk):
    item = ForecastAdjustment.objects.get(id=pk)
    if request.method == "POST":
        item.delete()
        c = CostCenterMonthlyForecastAdjustmentReport(BftStatusManager().fy(), BftStatusManager().period())
        c.insert_grouped_forecast_adjustment(c.sum_forecast_adjustments())
        return redirect("forecast-adjustment-table")
    context = {"object": item, "back": "forecast-adjustment-table"}
    return render(request, "core/delete-object.html", context)
