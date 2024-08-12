# BFT Reports

All reports available in the BFT are displayed in HTML format within the BFT web interface itself.  All reports are read-only and available to users that are logged in.

## Fundamental Reports
[Financial Structure](financial-structure.md)  

## National Procurement Reports
### Monthly Reports
[BMT Screening Report](bmt-screening.md)  
[Cost Center Monthly Allocation Report](costcenter-monthly-allocation.md)  
[Cost Center Monthly Forecast Adjustment Report](costcenter-monthly-forecast-adjustment.md)  
[Cost Center Monthly Forecast Line Item Report](costcenter-monthly-forecast-line-item.md)  
[Cost Center Monthly Encumbrance Report](costcenter-monthly-encumbrance.md)  
[Cost Center Monthly Plan Report](costcenter-monthly-plan.md)  

### In Year Report
[Cost Center In Year FEAR Report](costcenter-in-year-fear.md)  

## Capital Reports

[Forecasting Estimates Report](capital-forecasting-estimate.md)  
[Forecasting Year End Ratio Report](./capital-forecasting-year-end-ratio.md)  
[Forecasting FEAR Status Report](capital-forecasting-fear.md)  
[Forecasting Historical Outlook Report](capital-forecasting-historical-outlook.md)  
[Forecasting Dashboard Report](capital-forecasting-dashboard.md)  

## Allocation Reports

[Allocation Status](allocation-status.md)
## Warning Messages

When using the reports, the system attempts to provide as much as possible feedback to the user.  Typical messages will be displayed to inform the user when something goes wrong.

!!! Info "Cost Center YYYYYY does not exist."
    You provided a cost center that is not recorded in the database

!!! Info "Fund Center 2134AA does not exist."
    You provided a fund center that is not recorded in the database

!!! Info "Fund C1111 does not exist."
    You provided a fund that is not recorded in the database

!!! Info "There are no data to display"
    Given the selection criteria, no data was found.  This will obviously happen if say the fund center does not exist or there are no data yet for the given quarter.

!!! Info "19 is not a valid period. Expected value is one of 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14"
    Acceptable period values are between 1 and 14.
