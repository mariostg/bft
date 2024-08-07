# Line Items
!!! Todo "Need revision"
## Overview

The line item table is the entry door to line item forecasting. It displays all lines according to the applied [line item filter](#filtering-line-items).

<figure markdown>

_Line item table overview_
![](images/line-items-table.png)

</figure>

### Toggling Description and Comments

Line items descriptions and comments visibility can be toggled by clicking the Toggle long text view button located at the very top of the table.

### Filtering line items

The line item table can be filtered by mean of several fields as shown in the image below. Most available fields are free form text but the cost center which is a selection list. Many filter options used simultaneously narrow down the select. Thus select a cost center and a fund will show all lines that match the cost center <strong>AND</strong> the fund.

<figure markdown>

_Line item filtering options_
![](images/line-item-table-filter.png)

</figure>

## Forecasting Actions

The green buttons visible for each line item allows for forecasting actions. It is possible to forecast all lines for a single document (No XXXXXXX button), for a single cost center (8486B1 button) or for the line itself.

### Forecast by Document Number

<figure markdown>

_Forecast by Document Number Form will forecast all lines under specified document number_
![](images/form-document-item-forecast.png)

</figure>

With this input form, one can forecast all lines that fall under the selected document number by specifying a total amount for the document. Each line item will then be assigned a forecast proportionally taking into consideration spent and working plan of each line. Upon submission, user is redirected to the line item table which is filtered by document number for convenience.

### Forecast by Cost Center

<figure markdown>

_Forecasting by Cost Center Form will forecast all lines under specified cost center_
![](images/line-item-forecast-by-costcenter-form.png)

</figure>

With this input form, one can forecast all lines that fall under the selected cost center by specifying a total amount for the cost center. Each line item will then be assigned a forecast proportionally taking into consideration spent and working plan of each line. Upon submission, user is redirected to the line item table which is filtered by document number for convenience.

### Forecast individual line item

When the spent value is zero, it is possible to set the forecast to zero (Set to 0 button). If the spent is greater than zero, the button is not visible. Alternatively, to set the forecast equals to the working plan, one can use the button set to WP.

The Form Input button opens a form that allows for description and comment input as well as setting the forecast for the line item and some other fields as shown below.

<figure markdown>

_Individual line item forecasting form for updating all forecasting apects related to a single line item_
![](images/line-item-forecast-form.png)

</figure>

When doing individual line item forecast, messages will warn you if you attempt to forecast below the spent. Such an attempt will set the forecast to the spent amount. If you attempt to forecast above the working plan, the forecast will be set to the working plan.

<figure markdown>

_Attempt to forecast above working plan_
![](images/line-item-forecast-higher-than-workingplan-warning.png)

</figure>

## Uploading Line Items

Line items can be uploaded in the BFT in two manners. During BFT normal operations, a designated person performs the upload for the entire division on a daily basis and normally in the morning. This is known as an upload at the fund center level. Executing such an operation has the effect of creating "orphan lines". An orphan line is a line that exists in the BFT, but does not exist in the Encumbrance Report. Such orphan lines are not erased from the BFT, but their encumbrance and forecast are set to zero.

A more practical approach is to perform an upload the the cost center level. This operation can be executed by designated people who have the option to perform an upload at their convenience any time during the day. This approach will also create orphan lines, but for the targeted cost center only.

## Upload line items for Cost Center

The upload of a cost center necessitates a DND Cost Center Encumbrance Report from DRMIS and must contain specific columns with names as defined by DRMIS.

The report must contain only the lines for one single cost center which also mean only one fund center which must be the direct parent of the targeted cost center.

Both fund center and cost center must exist in the BFT.

<figure markdown>

Cost Center Lint Items Upload form will act on all line items related to the specified cost center
![](images/line-item-upload-by-costcenter-form.png){align=right}

</figure>

Three pieces of information are mandatory and must be supplied to the input form : The file that contains the encumbrance report, the fund center and the cost center, child of the fund center.

There are several checks that are performed when the proceed button is pressed and messages will be displayed if anything is not acceptable to the BFT.  The DRMIS report must be supplied as is without any alterations.

-   The fund center must exist in the BFT.
-   The cost center must be a child of the fund center.
-   All funds present in the report must exist in the BFT.
-   The report must contain only one fund center.
-   The report must contain only one cost center.
-   The report header must mention the base fiscal year.
-   The report header must mention the Funds center.
-   The report header as defined by DRMIS must indicate the same fund center as the one indicated in the input form.
-   The provided file must be a DND cost center encumbrance report. This information is part of the DRMIS report header.
-   The provided file must have a column header line that matches what the BFT expect.


If any of the above fails, the upload process will not take place.

During the upload process, the BFT will manipulate the line items in the following ways:

-   Lines found to be orphan will have their encumbrance and forecast set to zero.
-   A fund center integrity check is performed by comparing the fund center assigned to a line item with the fund center assigned to the cost center as defined in the BFT financial structure report. Discrepancies ([Wrong fund center](#wrong-fund-center)) will be indicated in the screening report
-   Lines without a document type will be assigned one based on the encumbrance type. Example, encumbrance type "Purchase Requisitions" will be assigned PC as document type.
-   When a line item is new, record its encumbrance for historical purposes.
-   Adjust the forecast of line items. When forecast is below spent, set the forecast to spent. When the forecast is above working plan, set the forecast to working plan

!!! Note
    If the encumbrance report has any line containing a fund center that does not exist in the BFT, download process will carry on normally. The Line Item Table will highlight discrepencies as shown below.

<figure markdown>

*BFT Screening report indicates potential problem in cost center/fund center relationship*
![](images/line-item-fund-center-incoherent.png)
</figure>

## Upload Messages


This is telling that the cost center parent in the financial structure of the BFT is different than one is being reported in the encumbrance report.  Either the BFT financial structure must be changed or there is a problem in DRMIS.

!!! Warning "The encumbrance report contains a fund that is not recorded in the BFT"

    ('There are missing funds', {'C444'})

!!! Warning "Uploading for one cost center, BFT Expect to find only one cost center in the encumbrance report"

    There are more that one cost center in the report. Found 8484WA, 8484ZZ

!!! Warning "Encumbrance report has a cost center that does not exists in the BFT"

    ('There are missing cost centers', {'8484ZZ'})

### Wrong fund center

If for a given line item there exist a discrepency between the fund center reported in the encubrance report and the BFT financial structure, incoherency will be reported in the line item view.

![Line item incoherent fund center](images/line-item-fund-center-incoherent.png "Line item incoherent fund center")
_Line item incoherent fund center_

If it can be determined that the fund center specified is not the direct parent of the specified cost center, the download will not occur.  The user will be warned as show below.

<figure markdown>

*Invalid fund center and cost center relationship when both exist in the BFT*
![](images/form-upload-line-items-costcenter-error.png)
</figure>

### Wrong Cost Center

If the specified cost center does not exist in the BFT, the download will not accur.  The user will be warned as shown below.

<figure markdown>

*The specified cost center does not exists*
![](images/forn-upload-line-item-unknown-costcenter.png)
</figure>
