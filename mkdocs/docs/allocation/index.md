# Allocation

Allocations are managed at both cost center and fund center level using the
appropriate entry form.  Creating or updating an allocation will update the monthly
allocation for the current FY and period.  Deleting an allocation
has no effect on the monthly forecast adjustment.

## Viewing Allocations

All current allocations can be viewed by anyone.  The report will appear different whether
or not the user is permitted to create, update or delete allocations. Viewing allocations
works the same way for both Cost Centers and Fund Centers.

*Read only mode*
![](images/allocation-view-read-only.png)

*Editable mode*
![](images/allocation-view.png)

It is possible to display the monthly monthly.  This data is for historical purposes and is never
deleted. FY and Period are mandatory fields.

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

![](images/allocation-costcenter-csv-sample.png)
</figure>

The first row contains the header and the name of the elements in the header must be exactly as shown here. If this is not respected, a warning message will be displayed to notify the user and the operation will abort.

### Cost center allocation upload form

The user select the file containing the cost centers to upload by using the ==cost center allocation upload form==

<figure markdown>

![](images/allocation-costcenter-upload-form.png)
</figure>

#### Upload messages

Upon clicking the proceed button, the BFT will process the request and display any messages according to circumstances. Such as the one below which indicates that the column header in the file are invalid.

!!! warning "Supplying a file that contains invalid column header yields this message"

    Cost centers upload by admin, Invalid columns header"

And there are more potential messages.

!!! warning "Indicating a quarter that does not match the quarter indicated in the file."

    Error allocation upload by admin, Quarter data does not match request (2 does not match 1)

!!! warning "Indicating a fiscal year that does not match the file content."

    FY request does not match dataset

!!! warning "The source file contains more that one quarter."

    Quarters not all matching. admin, 2023, 2

!!! warning "The source file contains an unknown fund"

    Fund(s) not found during check fund ['C11']

!!! warning "The source file contains an unknown cost center."

    Cost centers not found during check cost centers ['8484WW']

!!! warning "The source file contains duplicate cost center - fund pair."

    Saving cost center allocation {'costcenter': , 'fund': , 'fy': 2023, 'quarter': 2, 'amount': 20000.0, 'note': 'Note related to allocation 2184XA', 'owner': >} generates UNIQUE constraint failed: costcenter_costcenterallocation.fund_id, costcenter_costcenterallocation.costcenter_id, costcenter_costcenterallocation.quarter, costcenter_costcenterallocation.fy.
