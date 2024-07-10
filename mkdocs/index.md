# Business Forecasting Tool Documentation

## BFT Data

- [Allocation](docs/allocation/)
- [Capital Forecasting](docs/capital-forecasting)
- [Capital Project](docs/capitalproject/)
- [Cost Center](docs/costcenter/)
- [Forecast Adjustment ](docs/forecast-adjustment/)
- [Fund](docs/fund/)
- [Line Items](docs/line-items/)
- [Source](docs/source/)


## Preparing BFT for Initial Launch

This section supposes that BFT is already deployed to some kind of environment, the goal here being to feed initial data in the system.

Typical sequence of events would be as follow:

-   [upload Sources](docs/source/index.md#uploading-sources)
-   [upload Fund Centers](docs/fundcenter/index.md#upload-fund-center)
-   [upload Cost Centers](docs/costcenter/index.md#upload-cost-center)

This sequence is important because of the parent-child relationship that is built in the system. This means that in order to upload the cost centers, their parents (the fund centers) must be in the system. Additionally, the cost centers also rely on Sources et Funds.

All uploads can be performed through the BFT User Interface for users that are granted appropriate permissions.

The data must be available in CSV format. The first row must be the name of the column headings while respecting specific nomenclature.
