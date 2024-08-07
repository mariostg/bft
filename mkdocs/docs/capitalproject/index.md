# Capital Projects

## Viewing Capital Projects

Capital projects can be viewed by anyone.  The report will appear different
whether or not the user is permitted to create, update or delete
capital projects.

*Viewing Capital Project in edit mode*
![](images/capital-project-view.png)

*Viewing Capital Project in read only mode*
![](images/capital-project-view-read-only.png)

## Create Capital Project
Creating a capital project requires the project number, it's name and the parent fund center.  The fund center must be created first if it does not exists.

Checking the Is Updatable field ensures that the capital project's encumbrance will be updated during the DRMIS download.

Optionally select a procurement officer.  The selected procurement officer will be paired to the lines items that are under the given capital project.

<figure markdown>
<figcaption>
Capital project form for creating and updating data
</figcaption>

![](images/capital-project-form.png)
</figure>

## Delete Capital Project

A confirmation dialog will appear before proceding with a delete action.  Once the project is deleted, the user is redirected to the Capital Project View.

*Confirm the Fund Center deletion*
![](images/capital-project-delete.png)

## Upload Capital Project

!!! Note

    These operations requires administration privileges.

### Capital Project Source File
The Capital Project required source file contains 4 columns as shown in the sample below. The first three columns are mandatory : project_no, shortname and fundcenter.  The fund center must exist in the database otherwise the upload will fail.

<figure markdown>
<figcaption>
Capital Project Source File Sample
</figcaption>
![](images/capital-project-csv-sample.png)
</figure>

### Capital Project upload Form
The user select the file containing the capital projects to upload by using the capital project upload form.

![](images/capital-project-upload-form.png)

### Capital Project Upload Messages
!!! Todo
