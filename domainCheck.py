# The purpose of this tool is to check values in a feature class against the coded values in a geodatabase domain.
# The result will be a layer in ArcMap where values from the specified feature class and field that do not match
# the coded domain values are selected. This allows the user to easily identify illegal values and change them.
# This script intended to be used as the source of a script in a Python Toolbox (.tbx). It should be run in an open
# ESRI ArcMap map document (.mxd) via the ArcCatalog Window. The toolbox parameters should be (0) Feature Class and
# (1) Field. The Field parameter needs to be set to 'Obtained From' : Feature_Class.
#
# Created August 20, 2016
# Eric Delynko

import arcpy
import os

arcpy.env.overwriteOutput = True

mxd = arcpy.mapping.MapDocument("Current")

dfs = arcpy.mapping.ListDataFrames(mxd)
dataFrame = dfs[0].name
df = arcpy.mapping.ListDataFrames(mxd, "{}".format(dataFrame))[0]

# Get feature class to analyze
fc = arcpy.GetParameterAsText(0)
# Select field to analyze (field list should be automatically populated by Python tool)
fieldSel = arcpy.GetParameterAsText(1)

# Create Describe object from feature class
descFC = arcpy.Describe(fc)

# Define workspace
def get_workspace(featureClass):
    fcDesc = arcpy.Describe(featureClass)
    catalogPath = os.path.dirname(fcDesc.catalogPath)
    # Determines the workspace path based on whether feature class is in a feature dataset
    if arcpy.Describe(catalogPath).dataType == 'FeatureDataset':
        arcpy.env.workspace = arcpy.Describe(catalogPath).path
    else:
        arcpy.env.workspace = fcDesc.path
    return arcpy.env.workspace
get_workspace(fc)

# Create domain list object
doms = arcpy.da.ListDomains()

# Create empty list for domain coded values
domValList = []
# Create field list object
fieldList = arcpy.ListFields(fc)

# Get the domain of the selected field by comparing the name of the selected field to field list
# and getting the domain from that field
def get_domain_for_field():
    for field in fieldList:
        if fieldSel == field.name:
            fieldDom = field.domain
    return fieldDom
fieldDomain = get_domain_for_field()

if len(fieldDomain) > 0:
    print arcpy.AddWarning("The domain for the {} field is {}.\n".format(fieldSel, fieldDomain))
    # Get the coded values for domain of selected field
    for dom in doms:
        if dom.name == fieldDomain:
            cv = dom.codedValues
            for val, desc in cv.iteritems():
                domValList.append("{}".format(val))

    # Add feature class to map
    addLayer = arcpy.mapping.Layer(fc)
    arcpy.mapping.AddLayer(df, addLayer)

    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()

    # Create empty list object for values that do not match coded values in domain
    nonDomVals = []

    # Create list of layer in mxd which will include newly added layer
    lyrs = arcpy.mapping.ListLayers(mxd)

    # Create selection based on non-matching values
    for lyr in lyrs:
        # Determine that the layer in the mxd is pointing to the correct data
        if lyr.name == descFC.name:
            # Create Search Cursor for the layer
            cursor = arcpy.SearchCursor(lyr)
            for row in cursor:
                # Get the value of each cell in selected field
                value = row.getValue(fieldSel)
                # SQL query to select features
                qry = "{} = '{}'".format(fieldSel, value)
                if value is None:
                    # Select "<Null>" values and create selection (assumes Null values are not coded values in the domain)
                    arcpy.SelectLayerByAttribute_management(lyr, "ADD_TO_SELECTION", "{} IS NULL".format(fieldSel))
                elif value not in domValList:
                    # Adds values obtained from cells that do not match values in the coded value list to list
                    # of non-matching values
                    nonDomVals.append(value)
                    # Select values obtained from cells that do not match values in the coded value list (domValList)
                    arcpy.SelectLayerByAttribute_management(lyr, "ADD_TO_SELECTION", qry)

    # Create set from list of non-matching values
    nonDom = set(nonDomVals)
    if len(nonDomVals) < 1:
        print arcpy.AddWarning("Congratulations!! All values in the data match the domain's coded values.\n")
    # Print values in data that do not match coded values in selected field
    for v in nonDom:
        print arcpy.AddWarning("{} is not a value in the {} domain for the {} field.\n".format(v, fieldDomain, fieldSel))

    print arcpy.AddWarning("Valid values are for {} field are:".format(fieldSel))
    for domVal in domValList:
        print arcpy.AddWarning(domVal)

    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()
# Nothing happens if field has no domain
else:
    print arcpy.AddWarning("The {} field has no domain.".format(fieldSel))
