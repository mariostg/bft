# Preparing BFT for usage

This section supposes that BFT is already deployed to some kind of environment, the goal here being to feed initial data in the system.

Typical sequence of events would be as follow:

-   [upload Sources](./upload-sources.md)
-   [upload Fund Centers](./upload-fundcenters.md)
-   [upload Cost Centers](./upload-costcenters.md)

This sequence is important because of the parent-child relationship that is built in the system. This means that in order to upload the cost centers, their parents (the fund centers) must be in the system. Additionally, the cost centers also rely on Sources et Funds.

All uploads can be performed through the BFT User Interface for users that are granted appropriate permissions.

The data must be available in CSV format. The first row must be the name of the column headings while respecting specific nomenclature.
