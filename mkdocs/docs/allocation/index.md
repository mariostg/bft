# Allocation

Allocations are managed at both cost center and fund center level using the
appropriate entry form.  Creating or updating an allocation will update the monthly
allocation for the current FY and period.  Deleting an allocation
has no effect on the monthly allocation.

## Viewing Allocations

All current allocations can be viewed by anyone.  The report will appear different whether
or not the user is permitted to create, update or delete allocations. Viewing allocations
works the same way for both Cost Centers and Fund Centers.

*Read only mode*
![](images/allocation-view-read-only.png)

*Editable mode*
![](images/allocation-view.png)

It is possible to display the monthly allocation.  This data is for historical purposes for the last 5 years.
FY and Period are mandatory fields.

*Viewing monthly allocation*
![](images/allocation-monthly.png)

## Create Allocation

Creating an allocation requires the cost center, the fund, the FY, the quarter and
the amount of the allocation.  Amount of the allocation must be greather than zero.


!!! warning "It is not possible to create more than one allocation for a given cost center, fund, FY and period."

<figure markdown>
<figcaption>
Allocation form for creating and updating data
</figcaption>

![](images/allocation-form.png)
</figure>

## Delete Allocation

A confirmation dialog will appear before proceding with the delete action.


*Confirm the allocation deletion*
![](images/allocation-delete.png)

## Uploading Cost Center Allocations

!!! note

    This operation requires administration privileges.

### Source file

The required csv file must contains 6 columns as shown in the sample below.
The quarter column must be a number between 1 and 4. The amount numbers must not contain any separator other than the dot decimal separator. The note entries are not mandatory. The text must be surrounded by double quotes.

<figure markdown>
<figcaption>
Sample cost center allocation CSV file
</figcaption>
![](images/allocation-costcenter-csv-sample.png)
</figure>

The first row contains the header and the name of the elements in the header must be exactly as shown here. If this is not respected, a warning message will be displayed to notify the user and the operation will abort.

### Cost center allocation upload form

The user select the file containing the cost centers to upload by using the ==cost center allocation upload form==

<figure markdown>

![](images/allocation-costcenter-upload-form.png)
</figure>

### Cost Center Upload Messages

Upon clicking the proceed button, the BFT will process the request and display any messages according to circumstances. Such as the one below which indicates that the column header in the file are invalid.

!!! warning "Cost centers upload by admin, Invalid columns header"
    Upload will fail because it contains an invalid column header.  Verify the first row of the source file.  Maybe you selected the wrong file.

And there are more potential messages.

!!! warning "Error allocation upload by admin, Quarter data does not match request (2 does not match 1)"
    The quarter provided in the upload form does not match the quarter from the dataset

!!! warning "FY request does not match dataset"
    The FY provided in the upload form does not match the FY from the dataset

!!! warning "Quarters not all matching. admin, 2023, 2"
    The source file contains more that one quarter. Upload can be done only if the quarter column contains the save values.

!!! warning "Fund(s) not found during check fund ['C11']"
    The source file contains a fund that does not exist in the database.

!!! warning "Cost centers not found during check cost centers ['8484WW']"
    the source file contains a cost center that does not exist in the database.

!!! warning "Saving cost center allocation 8484YA - CELLAR - C113 - Basement Procurement - 2023 Q1 20000.99 generates UNIQUE constraint failed: bft_costcenterallocation.fund_id, bft_costcenterallocation.costcenter_id, bft_costcenterallocation.quarter, bft_costcenterallocation.fy."
    You are trying to save an allocation that already exist in the database for the given cost center, FY, quarter and fund.

## Uploading Fund Center Allocations

!!! note
    This operation requires administration privileges.

### Source file

The required csv file must contains 6 columns as shown in the sample below.
The quarter column must be a number between 1 and 4. The amount numbers must not contain any separator other than the dot decimal separator. The note entries are not mandatory. The text must be surrounded by double quotes.

<figure markdown>
<figcaption>
Sample fund center allocation CSV file
</figcaption>
![](images/allocation-fundcenter-csv-sample.png)
</figure>


The first row contains the header and the name of the elements in the header must be exactly as shown here. If this is not respected, a warning message will be displayed to notify the user and the operation will abort.

### fund center allocation upload form

The user select the file containing the fund centers to upload by using the ==fund center allocation upload form==

<figure markdown>

![](images/allocation-costcenter-upload-form.png)
</figure>

### Fund Center Upload Messages

!!! Warning "Fund center allocation upload by admin, Invalid columns header"
    Upload will fail because it contains an invalid column header.  Verify the first row of the source file.  Maybe you selected the wrong file.

!!! warning "Error allocation upload by admin, Quarter data does not match request (2 does not match 1)"
    The quarter provided in the upload form does not match the quarter from the dataset

!!! warning "FY request does not match dataset"
    The FY provided in the upload form does not match the FY from the dataset

!!! warning "Quarters not all matching. admin, 2023, 2"
    The source file contains more that one quarter.  Upload can be done only if the quarter column contains the save values.

!!! Warning "Fund(s) not found during check fund ['C222']"
    The source file contains a fund that does not exist in the database.

!!! Warning "Fund centers not found during check fund centers ['2184Z6']"
    the source file contains a fund center that does not exist in the database.

!!! Warning "Saving fund center allocation 2184DA - DAEME - C113 - Basement Procurement - 2023Q1 10.0 generates UNIQUE constraint failed: bft_fundcenterallocation.fund_id, bft_fundcenterallocation.fundcenter_id, bft_fundcenterallocation.quarter, bft_fundcenterallocation.fy"
    You are trying to save an allocation that already exist in the database for the given fund center, FY, quarter and fund.
