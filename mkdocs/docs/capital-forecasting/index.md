# Capital Forecasting

## Overview

Capital forecasting can be broken down into *New Year*, *In Year*, and *Year End*. Each have common fields : fund, fy, capital project, commit item and notes.

New Year capital forecasting contains the initial allocation.

In Year capital forecasting contains quarterly data for the following:

- allocation,
- spent,
- commitment,
- pre-commitment,
- fund reservation,
- low estimates,
- most likely estimates, and
- high estimates

Year end capital forecasting contains the year end spent.

## View Capital Forecasting

*Viewing Capital Forecasting In Year in edit mode*
![](images/capital-project-forecasting-in-year.png)

*Viewing Capital Forecasting In Year in read only mode*
![](images/capital-project-forecasting-in-year-read-only.png)

*Viewing capital forecasting New Year in edit mode*
![](images/capital-project-forecasting-new-year.png)

*Viewing capital forecasting New Year in read only mode*
![](images/capital-project-forecasting-new-year-read-only.png)

*Viewing capital forecasting Year End in edit mode*
![](images/capital-project-forecasting-year-end.png)

*Viewing capital forecasting Year End in read only mode*
![](images/capital-project-forecasting-year-end-read-only.png)

## Upload Capital Forecasting

!!! Note

    These operations requires administration privileges.

### New Year Upload
The new Year upload allows for fixing the allocations of each project for a given fund.
The project number and the fund must exist in the database for the upload to succeed.

#### New Year Source File

The New Year source file must contain 4 columns as shown in the sample below.  All fields are mandatory.  The columns initial_allocation and commit_item can be set to 0 if desired.

<figure markdown>
<figcaption>
Capital Forecasting New Year Source File Sample
</figcaption>
![](images/capital-project-forecasting-csv-new-year.png)
</figure>

#### New Year Messages

!!! Warning "Project c.123456 does not exist, no capital forecasts have been recorded."
    Your source file contains a project number that is not found in the database. Upload will fail if a project in the source file does not exist.

!!! Warning " New year capital project forecast upload. Invalid columns header"
    Upload will fail because it contains an invalid column header.  Verify the first row of the source file.  Maybe you selected the wrong file.

!!! Warning "Saving New Year Capital Forecasting C.999999 - BASEMENT RENO - 2020 - C113 generates UNIQUE constraint failed: bft_capitalnewyear.fund_id, bft_capitalnewyear.capital_project_id, bft_capitalnewyear.commit_item, bft_capitalnewyear.fy."

    Your project database already contains a New Year allocation for the specified project, FY and fund.

!!! Warning "Project C.999999 - BASEMENT RENO fund (c111) does not exist, no capital Forecasts have been recorded."
    The fund specified in the CSV file does not exist in the database.

### In Year Upload

The In Year upload allows for recording on a quarterly basis the encumbrance, allocation, estimates and encumbrance of each capital project.

#### In Year Source File

The In Year source file must contain 12 columns as shown in the sample below.

<figure markdown>
<figcaption>
Capital Forecasting In Year Source file Sample
</figcaption>
![](images/capital-project-forecasting-csv-in-year.png)
</figure>

#### In Year Messages

!!! Warning "Project c.123456 does not exist, no capital forecasts have been recorded."
    Your source file contains a project number that is not found in the database. Upload will fail if a project in the source file does not exist.

!!! Warning " New year capital project forecast upload. Invalid columns header"
    Upload will fail because it contains an invalid column header.  Verify the first row of the source file.  Maybe you selected the wrong file.

!!! Warning "Saving In Year Capital Forecasting C.999999 - BASEMENT RENO - 2020 - C113 generates UNIQUE constraint failed: bft_capitalinyear.fund_id, bft_capitalinyear.capital_project_id, bft_capitalinyear.commit_item, bft_capitalinyear.fy, bft_capitalinyear.quarter."

    Your project database already contains a New Year allocation for the specified project, FY and fund.


!!! Warning "Project C.999999 - BASEMENT RENO fund (c111) does not exist, no capital Forecasts have been recorded."
    The fund specified in the CSV file does not exist in the database.

### Year End Upload
The Year End Upload allows for recording the Year End Spent of each capital project by fund.

#### Year End Source File

<figure markdown>
<figcaption>
Capital Forecasting Year End Source File Sample
</figcaption>
![](images/capital-project-forecasting-csv-year-end.png)
</figure>

#### Year End Messages

!!! Warning "Project c.123456 does not exist, no capital forecasts have been recorded."
    Your source file contains a project number that is not found in the database. Upload will fail if a project in the source file does not exist.

!!! Warning " New year capital project forecast upload. Invalid columns header"
    Upload will fail because it contains an invalid column header.  Verify the first row of the source file.  Maybe you selected the wrong file.

!!! Warning "Saving Year End Capital Forecasting C.999999 - BASEMENT RENO - 2020 - C113 generates UNIQUE constraint failed: bft_capitalyearend.fund_id, bft_capitalyearend.capital_project_id, bft_capitalyearend.commit_item, bft_capitalyearend.fy."

    Your project database already contains a New Year allocation for the specified project, FY and fund.

!!! Warning "Project C.999999 - BASEMENT RENO fund (c111) does not exist, no capital Forecasts have been recorded."
    The fund specified in the CSV file does not exist in the database.

## Delete Capital Forecasting

!!! Todo
