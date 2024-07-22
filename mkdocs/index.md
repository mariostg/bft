# Business Forecasting Tool Documentation

## BFT Data
Each of the following sections contains the specific instructions about how to handle the data in the BFT.  Where applicable, it describes how to view, create, update, delete and upload the data.

- [Allocation](docs/allocation/index.md)
- [Capital Forecasting](docs/capital-forecasting/index.md)
- [Capital Project](docs/capitalproject/index.md)
- [Cost Center](docs/costcenter/index.md)
- [Forecast Adjustment ](docs/forecast-adjustment/index.md)
- [Fund](docs/fund/index.md)
- [Line Items](docs/line-items/index.md)
- [Source](docs/source/index.md)
- [Users](docs/user/index.md)

## Uploading Data in the BFT

Go to the specific section that explains how to upload in the BFT certain data from a CSV file.
[Upload Cost Center Allocations](docs/allocation/index.md#uploading-cost-center-allocations)  
[Upload Capital Forecasting New Year Allocation](docs/capital-forecasting/index.md#upload-capital-forecasting)
## Preparing BFT for Initial Launch

This section supposes that BFT is already deployed to some kind of environment, the goal here being to feed initial data in the system.

Typical sequence of events would be as follow:

-   [upload Sources](docs/source/index.md#uploading-sources)
-   [upload Fund Centers](docs/fundcenter/index.md#upload-fund-center)
-   [upload Cost Centers](docs/costcenter/index.md#upload-cost-center)

This sequence is important because of the parent-child relationship that is built in the system. This means that in order to upload the cost centers, their parents (the fund centers) must be in the system. Additionally, the cost centers also rely on Sources et Funds.

All uploads can be performed through the BFT User Interface for users that are granted appropriate permissions.

The data must be available in CSV format. The first row must be the name of the column headings while respecting specific nomenclature.
