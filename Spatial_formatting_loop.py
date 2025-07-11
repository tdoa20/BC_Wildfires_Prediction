# Import QGIS and geospatial processing libraries
import processing  # Enables access to QGIS's built-in processing toolbox algorithms
import sys
import os
import random
from datetime import datetime, timezone, timedelta  # For date/time operations
from qgis.analysis import QgsNativeAlgorithms  # Provides access to QGIS-native algorithms
from qgis.PyQt.QtCore import QVariant  # Used for defining attribute data types
from pyproj import Transformer  # Used to convert coordinates between projections
import re
import math
from osgeo import gdal  # Core GDAL library for raster I/O
from processing.core.Processing import Processing  # Initializes the QGIS processing framework
from qgis.core import (  # QGIS core classes used throughout the script
    QgsVectorLayer, QgsProject, QgsProcessingContext, 
    QgsProcessingFeedback, edit, QgsApplication, 
    QgsProcessingFeatureSourceDefinition, QgsRasterLayer,
    QgsRasterBandStats, QgsField, QgsFeature, QgsGeometry,
    QgsPointXY, QgsVectorFileWriter, 
    QgsCoordinateReferenceSystem, QgsProcessingProvider, QgsFields
)
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider  # GDAL algorithm access for processing
import csv  # Used for reading/writing tabular data
from collections import defaultdict  # For structured default dictionary use
from dateutil import parser  # To handle date parsing and formatting
import logging  # For tracking script progress and logging messages

# -------------------------------------------
# Initialize the QGIS Processing framework.
# This step is mandatory to use any of QGIS’s built-in tools via Python.
Processing.initialize()

# Register algorithm providers so we can call their tools later.
# Native QGIS tools and GDAL tools are required for operations like reprojecting or clipping.
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
QgsApplication.processingRegistry().addProvider(GdalAlgorithmProvider())

logging.info("✅ GDAL Processing tools enabled.")

# -------------------------------------------
# Define the base folder where all your shapefiles and raster files are stored
base_dir = 'C:/Users/tdoa2/OneDrive/Desktop/Data analytics/BCIT Data Analytics Certificate/BABI 9050/Code/Spatial data analysis/Spatial data cleaning'

# Define path to the Canada provinces shapefile (.shp is a common geospatial vector format)
canada_provinces_path = os.path.join(base_dir, 'Map_of_Canada/lpr_000b16a_e.shp')

# Load the shapefile as a vector layer. If it’s valid, it can be used for operations like filtering and clipping.
canada_layer = QgsVectorLayer(canada_provinces_path, 'Canada Provinces', 'ogr')


# Check whether the Canada provinces shapefile loaded successfully.
# QGIS layers can sometimes fail to load due to incorrect paths, corrupt files, or unsupported formats.

if not canada_layer.isValid():
    # If the layer is not valid, log an error message.
    logging.info("❌ Canada provinces layer failed to load.")
else:
    # If the layer is valid, log a success message.
    logging.info("✅ Canada provinces layer created.")

# Logging system
# Define the path to a log file where the script will record its activity.
log_path = os.path.join(base_dir, 'script_logs.log')

# Configure Python's logging module to write INFO-level logs to the file,
# with timestamps and messages included in each log entry.
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(message)s')


# --- Extract British Columbia boundary
# Define the output file path where the British Columbia boundary shapefile will be saved.
bc_output_path = os.path.join(base_dir, 'Map_of_Canada/BC_boundary.shp')

# Use QGIS's 'extract by attribute' tool to select British Columbia from the Canada shapefile.
# 'PREABBR' is the field containing province abbreviations (like 'B.C.').
# This process filters the national shapefile to isolate only British Columbia's geometry.
processing.run("native:extractbyattribute", {
    'INPUT': canada_layer,   # Input shapefile with all provinces
    'FIELD': 'PREABBR',      # Field to filter on (province abbreviation)
    'OPERATOR': 0,           # Operator 0 means 'equals'
    'VALUE': 'B.C.',         # Value to match (British Columbia)
    'OUTPUT': bc_output_path # Output path for the new shapefile
})
logging.info("✅ BC boundary extracted and saved to:", bc_output_path)


# --- Load BC layer
# Load the newly created British Columbia shapefile into QGIS as a vector layer.
bc_boundary_layer = QgsVectorLayer(bc_output_path, 'BC Boundary', 'ogr')

# Check if the layer loaded correctly.
# If it did, log a success message. If not, log a failure message.
if bc_boundary_layer.isValid():
    logging.info("✅ BC Boundary layer created.")
else:
    logging.info("❌ Failed to load BC Boundary layer.")

# === STEP: Reproject BC Boundary to EPSG:3347 ===
# Reprojection converts spatial data from one coordinate reference system (CRS) to another.
# EPSG:3347 is a common projected CRS for Canada, which allows for more accurate distance calculations.
reprojected_bc_boundary = os.path.join(base_dir, 'Map_of_Canada/BC_boundary_epsg3347.shp')

# Use QGIS to reproject the BC boundary shapefile from its original CRS to EPSG:3347.
processing.run("native:reprojectlayer", {
    'INPUT': bc_output_path,  # Path to the original BC shapefile
    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3347'),  # The target coordinate system
    'OUTPUT': reprojected_bc_boundary  # Output file path for the reprojected layer
})
logging.info("✅ Reprojected BC boundary to EPSG:3347")

# Load the newly reprojected shapefile into QGIS
bc_boundary_layer_3347 = QgsVectorLayer(reprojected_bc_boundary, 'BC Boundary (EPSG:3347)', 'ogr')

# Check if the reprojected layer loaded properly
if bc_boundary_layer_3347.isValid():
    QgsProject.instance().addMapLayer(bc_boundary_layer_3347)  # Add it to the map/project
    logging.info("✅ Reprojected BC boundary layer created successfully.")
else:
    logging.info("❌ Failed to load reprojected BC boundary layer.")

# --- Clip and reproject Fuel Raster
# Define file paths for the original and processed versions of the fuel type raster
fuel_raster_path = os.path.join(base_dir, 'National_FBP_Fueltypes_version2014b/nat_fbpfuels_2014b.tif')
clipped_raster_temp = os.path.join(base_dir, 'National_FBP_Fueltypes_version2014b/temp_clipped_fuel.tif')
final_clipped_raster = os.path.join(base_dir, 'National_FBP_Fueltypes_version2014b/BC_fuel_type_epsg3347.tif')

# Clip the national fuel type raster to the shape of British Columbia
# This isolates only the BC portion of the raster to reduce processing time and improve focus
processing.run("gdal:cliprasterbymasklayer", {
    'INPUT': fuel_raster_path,           # Original full raster
    'MASK': reprojected_bc_boundary,     # Use the BC boundary as the mask
    'SOURCE_CRS': None,                  # CRS is auto-detected
    'TARGET_CRS': None,
    'NODATA': -9999,                     # Assign -9999 to areas outside BC
    'ALPHA_BAND': False,
    'CROP_TO_CUTLINE': True,            # Crop the raster tightly to BC boundary
    'KEEP_RESOLUTION': True,            # Preserve original resolution
    'OPTIONS': '',
    'DATA_TYPE': 0,                     # Same data type as input
    'EXTRA': '',
    'OUTPUT': clipped_raster_temp        # Save temporary clipped raster
})
logging.info("✅ Temporary clipped fuel raster created.")

# If the clipping was successful and the temp file exists
if os.path.exists(clipped_raster_temp):
    # Reproject the clipped raster to EPSG:3347 to align it with other layers
    processing.run("gdal:warpreproject", {
        'INPUT': clipped_raster_temp,
        'SOURCE_CRS': None,
        'TARGET_CRS': 'EPSG:3347',
        'RESAMPLING': 0,                 # Nearest neighbor resampling for categorical data
        'NODATA': None,
        'TARGET_RESOLUTION': None,
        'OPTIONS': '',
        'DATA_TYPE': 0,
        'TARGET_EXTENT': None,
        'TARGET_EXTENT_CRS': None,
        'MULTITHREADING': False,
        'OUTPUT': final_clipped_raster   # Final output raster
    })
    logging.info("✅ Reprojected raster to EPSG:3347 successfully.")

    # Load the reprojected fuel raster as a QGIS layer
    reprojected_fuel_layer = QgsRasterLayer(final_clipped_raster, "BC Fuel Type (EPSG:3347)")
    if reprojected_fuel_layer.isValid():
        logging.info("✅ Reprojected raster added to project.")
        QgsProject.instance().addMapLayer(reprojected_fuel_layer)
    else:
        logging.info("❌ Failed to load reprojected raster.")
else:
    logging.info(f"❌ File not found: {clipped_raster_temp}")
    
    
    
# === PARAMETERS
start_year = 2000
end_year = 2024
# These two variables define the time range (in years) for the wildfire analysis.
# The script will loop through each year from 2000 to 2024.

# --- Months dictionary
month_words = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}
# This dictionary converts numeric month values (e.g. 1) into human-readable names (e.g. "January").
# It is useful for labeling outputs or organizing files by month.

# -- Total fires
fire_counts = {}  # This dictionary will store how many fire points were found for each (year, month).
non_fire_counts = {}  # This will store how many non-fire (random) points should be generated for each (year, month).
yearly_fire_counts = defaultdict(list)  # This will hold lists of monthly fire counts for each year (for averaging later).

# Store all reprojected layers so we don't recompute
reprojected_hotspot_layers = {}
# This dictionary caches reprojected hotspot layers per year to avoid repeating the reprojection process,
# which saves time and computing resources.

# BC Boundary features
spatial_index = QgsSpatialIndex(bc_boundary_layer_3347.getFeatures())
# A spatial index is a data structure that helps QGIS quickly find features (like regions or polygons) that
# intersect with a given point or geometry. It speeds up spatial queries.

boundary_features = {f.id(): f for f in bc_boundary_layer_3347.getFeatures()}
# This creates a dictionary of all features (geometric shapes) in the BC boundary layer,
# keyed by their unique ID. This allows fast lookup of boundary features during point-in-polygon checks,
# such as when generating random points within BC.



# == FUNCTIONS
# -- Get fire hotspots files
def get_hotspots(year):
    # Load the shapefile that contains fire hotspot points for a specific year.
    # Each shapefile has information about where and when fires occurred.
    hotspot_path = os.path.join(base_dir, f"Point_data/Hotspot data/{year}_hotspots/{year}_hotspots.shp")
    hotspot_layer = QgsVectorLayer(hotspot_path, f"Hotspots {year}", 'ogr')  # Load using the OGR driver (used for vector files)
    
    # Check if the layer loaded correctly
    if not hotspot_layer.isValid():
        logging.info("❌ Hotspot shapefile failed to load.")
        return
    else:
        logging.info(f"✅ {year} Hotspot layer created.")
    return hotspot_layer  # Return the loaded vector layer of fire points

    
def reproject_hotspot_layer(hotspot_layer, year):
    # Reprojects the hotspot layer to a different coordinate system (EPSG:3347) 
    # to ensure consistency with other geographic layers like climate or fuel maps.
    
    reprojected_hotspot_folder = os.path.join(base_dir, f"Point_data/Hotspot data/{year}_hotspots/Reprojected_hotspot_files")
    os.makedirs(reprojected_hotspot_folder, exist_ok=True)
    reprojected_hotspot_path = os.path.join(reprojected_hotspot_folder, f"{year}_reprojected.shp")

    # Only perform reprojection if the file doesn't already exist
    if not os.path.exists(reprojected_hotspot_path):
        processing.run("native:reprojectlayer", {
            'INPUT': hotspot_layer,  # original data
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3347'),  # target coordinate system
            'OUTPUT': reprojected_hotspot_path  # file to save the reprojected layer
        })
        logging.info(f"✅ Reprojected hotspot layer for {year} saved.")
    else:
        logging.info(f"ℹ️ Reprojected hotspot file for {year} already exists.")

    # Load and return the reprojected hotspot layer
    reprojected_hotspot_layer = QgsVectorLayer(reprojected_hotspot_path, f"Reprojected {year} Hotspots", 'ogr')
    if not isinstance(reprojected_hotspot_layer, QgsVectorLayer):
        logging.error("❌ Input is not a vector layer. Make sure to pass a QgsVectorLayer, not a raster.")
        return None
    return reprojected_hotspot_layer

def get_monthly_hotspot_data(month_num, month_name, year, reprojected_hotspot_layer):
    # Extracts and filters fire hotspot data to only include points from a specific year and month.
    
    # Identify the name of the date field used in the layer
    field_names = [field.name() for field in reprojected_hotspot_layer.fields()]
    if 'REP_DATE' in field_names:
        date_field = 'REP_DATE'
    elif 'rep_date' in field_names:
        date_field = 'rep_date'
    else:
        logging.info(f"⚠️ {year} hotspot layer: No REP_DATE or rep_date field.")
        return None

    # Filter hotspot features to include only those with a date matching the specified month and year
    selected_features = []
    for feature in reprojected_hotspot_layer.getFeatures():
        try:
            raw_date = feature[date_field]
            if not raw_date:
                continue
            date_obj = parser.parse(str(raw_date))  # Convert the date text into a date object
            if date_obj.year == year and date_obj.month == month_num:
                selected_features.append(feature)
        except Exception as e:
            logging.info(f"⚠️ Skipping feature with bad date: {raw_date}, error: {e}")

    # If no features match the criteria, return None
    if not selected_features:
        logging.info(f"⚠️ {month_name} {year}: No features matched the date.")
        return None

    # Prepare a list of new features with correct geometry and attributes
    new_features = []
    for feat in selected_features:
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue
        new_feat = QgsFeature()
        new_feat.setFields(reprojected_hotspot_layer.fields())
        new_feat.setGeometry(QgsGeometry(geom))  # Create a deep copy of the geometry
        for field in reprojected_hotspot_layer.fields():
            new_feat.setAttribute(field.name(), feat[field.name()])
        new_features.append(new_feat)

    # Create a new temporary memory layer to store the filtered features, using the correct coordinate system (EPSG:3347)
    temp_layer = QgsVectorLayer("Point?crs=EPSG:3347", f"{year}_{month_name}_Hotspots", "memory")
    temp_layer.dataProvider().addAttributes(reprojected_hotspot_layer.fields())
    temp_layer.updateFields()
    temp_layer.dataProvider().addFeatures(new_features)
    temp_layer.updateExtents()

    # Check that the new layer is valid
    if temp_layer.isValid():
        logging.info(f"ℹ️ {month_name} {year}: Filtered layer has {temp_layer.featureCount()} features.")
    else:
        logging.info(f"❌ {month_name} {year} layer is not valid.")
        return None

    # Clip the filtered hotspots to the BC boundary so that only points inside the province are kept
    if not bc_boundary_layer_3347.isValid():
        logging.info("❌ BC boundary layer is not valid.")
        return None

    result = processing.run("native:clip", {
        'INPUT': temp_layer,  # Layer with filtered features
        'OVERLAY': bc_boundary_layer_3347,  # Clip layer (BC boundary)
        'OUTPUT': 'memory:'  # Store result in memory (not saved to file)
    })
    clipped_layer = result['OUTPUT']

    # If the clipped layer is empty, log a warning
    if clipped_layer.featureCount() == 0:
        logging.info(f"⚠️ {month_name} {year}: Clipped layer has no features.")
        return None

    # Final preparations for the output layer
    clipped_layer.setName(f"Hotspots {month_name} {year} EPSG:3347")
    clipped_layer.updateExtents()

    logging.info(f"✅ {month_name} {year}: Final layer has {clipped_layer.featureCount()} features.")
    return clipped_layer  # Return the final filtered and clipped hotspot layer


# Get climate data
def get_climate_raster_path(year, month_name):
    # This function constructs the file path to a climate raster file 
    # for a specific year and month. A raster is a grid of pixels, each
    # storing a value like temperature or precipitation at a specific location.
    
    # Step 1: Build the path to the folder that contains climate raster bands
    # The folder structure is organized by year and month.
    band_folder = os.path.join(
        base_dir,  # Base directory where all files are stored
        f"climate_data/GRIB_climate_data/{year}/{month_name}/Filled_Bands_{month_name}_{year}"
    )

    # Step 2: Define the filename of the stacked climate raster
    # This file combines several climate variables into one multi-layer raster.
    climate_stack = os.path.join(band_folder, f"{month_name}_{year}_Filled_Stacked_Climate.tif")

    # Step 3: Check if the raster file exists. If not, log an error and return None.
    if not os.path.exists(climate_stack):
        logging.info(f"❌ Missing climate raster: {climate_stack}")
        return None, None

    # Step 4: If the file exists, return the path to it.
    return climate_stack




# -- Generate random non-fire points
def gen_non_fire_points(year, month_name, non_fire_count):
    """
    Generates random non-fire points within the BC boundary.

    Parameters:
    - year (int): The year for which points are being generated.
    - month_name (str): Month name (e.g., 'January').
    - non_fire_count (int): Number of non-fire points to generate (either equal to fire count or 400).
    
    Returns:
    - QgsVectorLayer: The generated random points layer.
    """

    # Create folder to store the generated shapefile
    random_pts_dir = os.path.join(base_dir, f"Point_data/Random_points/{year}/{month_name}")
    os.makedirs(random_pts_dir, exist_ok=True)

    # Set the projection system to use: EPSG:3347 (a coordinate system suitable for Canada)
    target_crs = QgsCoordinateReferenceSystem('EPSG:3347')

    # Path where the shapefile with random points will be saved
    output_path = os.path.join(random_pts_dir, f"Random_NoFire_{month_name}_{year}.shp")

    # Check if the BC boundary layer is valid
    if not bc_boundary_layer_3347.isValid():
        logging.info("❌ BC boundary layer is not valid.")
        return None

    # Get the extent (bounding box) of the BC boundary layer to know the area to generate points in
    extent = bc_boundary_layer_3347.extent()
    xmin, xmax, ymin, ymax = extent.xMinimum(), extent.xMaximum(), extent.yMinimum(), extent.yMaximum()

    # Prepare a coordinate transformer to convert coordinates into latitude/longitude (EPSG:4326)
    transformer = Transformer.from_crs("EPSG:3347", "EPSG:4326", always_xy=True)

    # Create a memory layer to store the randomly generated non-fire points
    layer = QgsVectorLayer(f"Point?crs={target_crs.authid()}", f"Random_NoFire_{month_name}_{year}", "memory")
    provider = layer.dataProvider()

    # Define the attribute fields for each random point
    common_fields = [
        QgsField("Latitude", QVariant.Double),
        QgsField("Longitude", QVariant.Double),
        QgsField("Month", QVariant.String),
        QgsField("Year", QVariant.Int),
        QgsField("Fire", QVariant.Int)
    ]
    provider.addAttributes(common_fields)
    layer.updateFields()

    # Randomly generate points within the extent until the desired number is reached
    features = []
    tries = 0
    max_tries = 10000  # Prevent infinite loops if the area is too small

    while len(features) < non_fire_count and tries < max_tries:
        # Generate a random x and y coordinate within the extent
        x = random.uniform(xmin, xmax)
        y = random.uniform(ymin, ymax)
        point = QgsPointXY(x, y)
        geom = QgsGeometry.fromPointXY(point)

        # Use a spatial index to check if the point falls inside BC's actual polygon shape
        ids = spatial_index.intersects(geom.boundingBox())
        if any(boundary_features[i].geometry().contains(geom) for i in ids):
            # Convert coordinates to lat/lon for the attribute table
            lon, lat = transformer.transform(x, y)
            feat = QgsFeature()
            feat.setGeometry(geom)
            feat.setAttributes([lat, lon, month_name, year, 0])  # Fire = 0 (non-fire)
            features.append(feat)
        tries += 1

    # Add the generated features to the memory layer
    provider.addFeatures(features)
    layer.updateExtents()

    # Log how many points were successfully generated
    if len(features) < non_fire_count:
        logging.info(f"⚠️ Only generated {len(features)} of {non_fire_count} points after {max_tries} attempts.")
    else:
        logging.info(f"✅ Successfully generated {non_fire_count} no-fire points for {month_name} {year}.")

    # Save the layer as a shapefile to disk
    QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", target_crs, "ESRI Shapefile")
    logging.info(f"✅ Random no-fire layer saved: {output_path}")

    return layer, common_fields, transformer, target_crs


# === Clean hotspot layer
def rebuild_hotspot_clean_copy(clipped_layer, common_fields):

    # If there's no input layer, exit early
    if clipped_layer is None:
        logging.info("ℹ️ No fire points to clean.")
        return None

    # If the layer is invalid (corrupt or empty), exit early
    if not clipped_layer.isValid():
        logging.info("❌ Hotspot layer is not valid.")
        return None

    logging.info("🔁 Creating clean memory copy...")

    # Create a new memory layer to store the cleaned fire points
    cleaned_layer = QgsVectorLayer(f"Point?crs={clipped_layer.crs().authid()}", "Cleaned_Hotspot", "memory")
    provider = cleaned_layer.dataProvider()
    provider.addAttributes(common_fields)
    cleaned_layer.updateFields()

    # Determine actual field names for date and coordinates (could vary)
    original_fields = clipped_layer.fields().names()
    lat_name = 'LAT' if 'LAT' in original_fields else 'lat'
    lon_name = 'LON' if 'LON' in original_fields else 'lon'
    date_name = 'REP_DATE' if 'REP_DATE' in original_fields else 'rep_date'

    # Loop through features (fire points) and extract clean, consistent attributes
    for feat in clipped_layer.getFeatures():
        try:
            rep_date = feat[date_name]
            if "/" in rep_date:
                dt = datetime.strptime(rep_date, "%Y/%m/%d %H:%M:%S.%f")
            else:
                dt = datetime.strptime(rep_date, "%Y-%m-%d %H:%M:%S")
            month = dt.strftime('%B')
            year = dt.year
        except Exception as e:
            logging.info(f"⚠️ Failed date parsing for feature ID {feat.id()}: {e}")
            month, year = '', 0

        lat = feat[lat_name]
        lon = feat[lon_name]

        new_feat = QgsFeature()
        new_feat.setGeometry(feat.geometry())
        new_feat.setAttributes([lat, lon, month, year, 1])  # Fire = 1
        provider.addFeature(new_feat)

    cleaned_layer.updateExtents()
    logging.info("✅ Cleaned hotspot layer built and loaded.")
    return cleaned_layer


def reorder_hotspots(cleaned_layer, layer, transformer, common_fields):
    # If no cleaned fire layer is provided, exit early
    if cleaned_layer is None:
        logging.info("ℹ️ No fire points to reorder.")
        return None

    # Create a memory layer to store reordered hotspot points
    reordered_hotspot = QgsVectorLayer(f'Point?crs={cleaned_layer.crs().authid()}', "Reordered_Hotspot", "memory")
    provider_hotspot = reordered_hotspot.dataProvider()
    provider_hotspot.addAttributes(common_fields)
    reordered_hotspot.updateFields()
    
    # Add fire points to this new layer
    for feat in cleaned_layer.getFeatures():
        f = QgsFeature()
        f.setGeometry(feat.geometry())
        f.setAttributes([
            feat['Latitude'], feat['Longitude'], feat['Month'], feat['Year'], feat['Fire']
        ])
        provider_hotspot.addFeature(f)
    
    reordered_hotspot.updateExtents()
    logging.info("✅ Reordered hotspot layer created.")

    # Update coordinates for non-fire points by re-transforming geometry
    with edit(layer):
        lat_idx = layer.fields().indexOf("Latitude")
        lon_idx = layer.fields().indexOf("Longitude")
        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom and not geom.isMultipart():
                x, y = geom.asPoint()
                lon, lat = transformer.transform(x, y)
                feature.setAttribute(lat_idx, lat)
                feature.setAttribute(lon_idx, lon)
                layer.updateFeature(feature)

    logging.info("✅ Recalculated WGS84 coordinates for non-fire layer.")
    return reordered_hotspot


# -- MERGE fire and non-fire data points
def merge_data_points(month_name, year, month_num, reordered_hotspot, layer, common_fields, target_crs):
    # Decide which coordinate system (CRS) to use — prefer the fire layer if available
    base_crs = reordered_hotspot.crs().authid() if reordered_hotspot else layer.crs().authid()

    # Create the folder where the merged output will be saved
    merged_output_folder = os.path.join(base_dir, f"Point_data/Merged/{year}/{month_name}")
    os.makedirs(merged_output_folder, exist_ok=True)

    # Set the file path for the merged shapefile
    merged_path = os.path.join(merged_output_folder, f"Merged_Fire_NoFire_{month_name}_{year}.shp")

    # Create a temporary (in-memory) vector layer to store merged points
    merged_layer = QgsVectorLayer(f'Point?crs={base_crs}', "Merged", "memory")
    merged_provider = merged_layer.dataProvider()

    # Define the structure of the attributes (columns)
    merged_provider.addAttributes(common_fields)
    merged_layer.updateFields()

    # Add features from both the fire and non-fire layers to the merged layer
    for src_layer in [reordered_hotspot, layer]:  # Fire points first, then non-fire
        if src_layer is not None:
            for feat in src_layer.getFeatures():
                f = QgsFeature()
                f.setGeometry(feat.geometry())  # Copy the geometry (coordinates)
                f.setAttributes([  # Set the attribute values from the source feature
                    feat['Latitude'], feat['Longitude'], feat['Month'], feat['Year'], feat['Fire']
                ])
                merged_provider.addFeature(f)

    # Update the spatial boundaries of the merged layer
    merged_layer.updateExtents()

    # Save the in-memory merged layer as a physical shapefile to disk
    QgsVectorFileWriter.writeAsVectorFormat(merged_layer, merged_path, "UTF-8", target_crs, "ESRI Shapefile")

    # Log whether the shapefile was successfully written
    if os.path.exists(merged_path):
        logging.info(f"✅ Merged dataset saved to: {merged_path}")
    else:
        logging.info("❌ Failed to write merged shapefile.")
    
    return merged_layer


# -- Rename automatically assigned raster band fields to readable names
def rename_climate_fields(layer, rename_map):
    """
    Takes a vector layer that contains raster sampling results and renames
    generic band names (e.g., Band_1) to descriptive names (e.g., temperature).
    """
    
    # Start editing the layer if it's not already editable
    if not layer.isEditable():
        layer.startEditing()

    # Get the list of existing field names
    fields = layer.fields()

    # Loop through each rename mapping (e.g., Band_1 ➝ temp_2m)
    for old_name, new_name in rename_map.items():
        idx = fields.indexOf(old_name)  # Get the index of the old name
        if idx != -1:
            logging.info(f"🔤 Renaming {old_name} ➜ {new_name}")
            layer.renameAttribute(idx, new_name)
        else:
            logging.info(f"⚠️ Field {old_name} not found in layer")

    # Save the changes
    layer.commitChanges()



# == POINT SAMPLING TIME!
def point_sampling(month_name, year, merged_layer, climate_stack):
    # === Output setup ===
    # Create a folder path and output file name to store sampled point shapefile for the given month and year
    sampled_output_folder = os.path.join(base_dir, f"Point_data/Sampled/{year}/{month_name}")
    os.makedirs(sampled_output_folder, exist_ok=True)
    sampled_output_path = os.path.join(sampled_output_folder, f"Sampled_Points_{month_name}{year}.shp")

    # === Temporary paths ===
    # Define temporary file paths to hold intermediate sampling results
    temp_input_path = os.path.join(sampled_output_folder, "temp_input_points.shp")
    temp_climate_sampled_path = os.path.join(sampled_output_folder, "temp_climate_sampled.shp")

    # === Save input merged layer to shapefile ===
    # Save the merged fire and non-fire point layer as a temporary shapefile so it can be sampled
    QgsVectorFileWriter.writeAsVectorFormat(merged_layer, temp_input_path, "UTF-8", merged_layer.crs(), "ESRI Shapefile")

    # === Load climate raster layer as QgsRasterLayer objects ===
    # Load the multi-band climate raster (e.g., temperature, wind) for use in sampling
    climate_raster = QgsRasterLayer(climate_stack, f"Climate Raster_{month_name}_{year}")
    if not climate_raster.isValid():
        logging.error(f"❌ Invalid climate raster: {climate_stack}")
        return None, None, sampled_output_folder

    # Ensure the fuel raster has been correctly loaded beforehand
    if not reprojected_fuel_layer.isValid():
        logging.error(f"❌ Invalid fuel raster: {fuel_raster_path}")
        return None, None, sampled_output_folder

    # === Sample climate stack ===
    # Use the "Raster Sampling" tool to attach climate values (from each raster band) to the input points
    processing.run("native:rastersampling", {
        'INPUT': temp_input_path,            # Input points to sample
        'RASTERCOPY': climate_raster,        # Raster to sample from
        'COLUMN_PREFIX': '',                 # Leave output columns without a prefix
        'OUTPUT': temp_climate_sampled_path  # Save output to temporary path
    })

    # === Sample fuel raster ===
    # Use the same sampling tool to attach fuel type data to each point
    processing.run("native:rastersampling", {
        'INPUT': temp_climate_sampled_path,    # Points that now have climate data
        'RASTERCOPY': reprojected_fuel_layer,  # Raster with fuel types
        'COLUMN_PREFIX': 'Fuel_',             # Prefix for fuel columns
        'OUTPUT': sampled_output_path         # Final output shapefile with all attributes
    })

    logging.info(f"✅ Sampled points saved to: {sampled_output_path}")

    # === Rename fields ===
    # Load the sampled shapefile and rename its generic column names (e.g., '1', '2') to meaningful names
    sampled_layer = QgsVectorLayer(sampled_output_path, "Sampled Points", "ogr")
    if not sampled_layer.isValid():
        logging.error(f"❌ Failed to load sampled layer: {sampled_output_path}")
        return None, None, sampled_output_folder

    # Mapping of original raster band names to user-friendly names
    rename_map = {
        '1': 'u10_wind',
        '2': 'v10_wind',
        '3': 'dew_temp_2m',
        '4': 'temp_2m',
        '5': 'tot_precip',
        '6': 'lai_high',
        'Fuel_1': 'Fuel_Type'
    }

    # Apply the renaming
    rename_climate_fields(sampled_layer, rename_map)

    return sampled_layer, None, sampled_output_folder


# -- Clean missing values
def clean_sampled_layer(sampled_layer):
    """Removes features with missing climate or fuel data."""
    
    # Create a new in-memory vector layer with the same coordinate system as the input
    crs = sampled_layer.crs().authid()
    clean_layer = QgsVectorLayer(f"Point?crs={crs}", "Cleaned Sampled Points", "memory")
    clean_provider = clean_layer.dataProvider()
    
    # Copy the same fields from the input layer
    clean_provider.addAttributes(sampled_layer.fields())
    clean_layer.updateFields()

    # Fields to check for missing data
    fields_to_check = [
        'u10_wind', 'v10_wind', 'dew_temp_2m', 'temp_2m',
        'tot_precip', 'lai_high', 'Fuel_Type'
    ]

    # Only keep fields that actually exist in the data (in case of mismatches)
    valid_fields = [f.name() for f in sampled_layer.fields()]
    fields_to_check = [f for f in fields_to_check if f in valid_fields]

    removed = 0  # Track number of removed features

    # Loop through all features in the layer and filter out incomplete ones
    for feat in sampled_layer.getFeatures():
        has_null = any(
            feat[field] in [None, '', -9999] or
            (isinstance(feat[field], float) and math.isnan(feat[field]))
            for field in fields_to_check
        )
        if has_null:
            removed += 1
            continue

        # If all required fields are valid, copy feature to clean layer
        clean_feat = QgsFeature()
        clean_feat.setGeometry(feat.geometry())
        clean_feat.setAttributes(feat.attributes())
        clean_provider.addFeature(clean_feat)

    logging.info(f"✅ Filtered out {removed} features with missing values.")
    logging.info(f"📦 Remaining features: {clean_layer.featureCount()}")

    # Add clean layer to QGIS map view
    QgsProject.instance().addMapLayer(clean_layer)

    return clean_layer


# === Save as CSV ===
def save_point_file(year, month_name, clean_layer, sampled_output_folder):
    # Define output CSV file path
    csv_output_path = os.path.join(sampled_output_folder, f"Cleaned_Sampled_Points_{month_name}{year}.csv")
    
    # Write the clean vector layer to CSV, including point geometry as X,Y coordinates
    QgsVectorFileWriter.writeAsVectorFormat(
        clean_layer, csv_output_path, "UTF-8", clean_layer.crs(), "CSV", layerOptions=['GEOMETRY=AS_XY']
    )

    # Confirm if the file was saved successfully
    if os.path.exists(csv_output_path):
        logging.info(f"✅ Cleaned attribute table saved to CSV: {csv_output_path}")
    else:
        logging.info("❌ Failed to save CSV file.")
        
    return csv_output_path





#== LOOP THROUGH DIFFERENT YEARS AND MONTHS
# This loop processes data year by year and month by month, starting from 'start_year' to 'end_year'
for year in range(start_year, end_year + 1):
    logging.info(f"Processing {year}...")

    # Load the fire hotspot data (point locations of fires) for the current year
    hotspot_layer = get_hotspots(year)

    # Reproject the hotspot data to a specific coordinate system (EPSG:3347) for spatial analysis
    reprojected_hotspot_layer = reproject_hotspot_layer(hotspot_layer, year)
    # Store reprojected layer in a dictionary to avoid reprocessing later
    reprojected_hotspot_layers[year] = reprojected_hotspot_layer

    # Now process each month (January to December)
    for month_num, month_name in month_words.items():
        # Retrieve the reprojected hotspot layer for the current year
        reprojected_hotspot_layer = reprojected_hotspot_layers[year]

        # Get the fire points that occurred in this specific month and year, clipped to BC’s boundary
        fire_points = get_monthly_hotspot_data(month_num, month_name, year, reprojected_hotspot_layer)

        # If no fire points exist for this month, log and skip further fire-related processing
        if fire_points is None:
            logging.info(f"⚠️ Skipping {month_name} {year} — no valid hotspot data.")
            fire_counts[(year, month_name)] = 0
            non_fire_counts[(year, month_name)] = None
            continue

        # Count how many fire points were found
        fire_count = len(fire_points)
        fire_counts[(year, month_name)] = fire_count

        # Store the fire count (used later to determine how many non-fire points to generate)
        if fire_count > 0:
            non_fire_counts[(year, month_name)] = fire_count
            yearly_fire_counts[year].append(fire_count)
        else:
            # Placeholder if there were no fires — we’ll compute an average later
            non_fire_counts[(year, month_name)] = None

# After first pass, calculate the average monthly fire count for each year (to use when no fires are present)
yearly_avg_fire = {
    year: int(round(sum(counts) / len(counts))) if counts else 400
    for year, counts in yearly_fire_counts.items()
}

# For each month, if no fires occurred, set non-fire count to that year’s average
# (or fallback to 400 if there’s no data at all)
for (year, month_name), count in fire_counts.items():
    if count > 0:
        non_fire_counts[(year, month_name)] = count
    else:
        non_fire_counts[(year, month_name)] = yearly_avg_fire.get(year, 400)

# Initialize a list to store paths to all final CSV outputs
all_csv_paths = []

# === Second pass: process each month’s data with full logic now that we know how many non-fire points to use
for year in range(start_year, end_year + 1):
    logging.info(f"Processing {year}...")

    # Load hotspot shapefile again for this year
    hotspot_layer = get_hotspots(year)

    for month_num, month_name in month_words.items():
        # Get the already-reprojected hotspot layer for this year
        reprojected_hotspot_layer = reprojected_hotspot_layers[year]

        # Get fire points for the current year and month
        fire_points = get_monthly_hotspot_data(month_num, month_name, year, reprojected_hotspot_layer)

        # Continue workflow even if there are no fire points (for balance, we still include non-fire points)
        if fire_points is None:
            logging.info(f"ℹ️ No fire points found for {month_name} {year}. Proceeding with non-fire data only.")

        # Step 2: Create random non-fire points equal to the number of fire points or average count
        non_fire_count = non_fire_counts[(year, month_name)]
        layer, common_fields, transformer, target_crs = gen_non_fire_points(year, month_name, non_fire_count)

        # Step 3: Clean and standardize the fire point attributes (e.g., extract date, coordinates)
        cleaned_layer = rebuild_hotspot_clean_copy(fire_points, common_fields)

        # Step 4: Ensure fire data is properly formatted and lat/lon values are recalculated
        reordered_hotspot = reorder_hotspots(cleaned_layer, layer, transformer, common_fields)

        # Step 5: Combine fire and non-fire points into a single shapefile for further analysis
        merged_layer = merge_data_points(month_name, year, month_num, reordered_hotspot, layer, common_fields, target_crs)

        # Step 6: Load the climate raster file for this month and year
        climate_stack = get_climate_raster_path(year, month_name)

        # Step 7: Sample climate and fuel values at each point location
        sampled_layer, _, sampled_output_folder = point_sampling(month_name, year, merged_layer, climate_stack)

        # Step 8: Remove any points with missing or invalid values from the sampled layer
        clean_layer = clean_sampled_layer(sampled_layer)

        # Step 9: Save the final cleaned data as a CSV file for later use in analysis
        csv_output_path = save_point_file(year, month_name, clean_layer, sampled_output_folder)
        all_csv_paths.append(csv_output_path)

        # Step 10: Log progress
        logging.info(f"Completed processing for {month_name} {year}")




# Combine all sampled monthly data into one CSV

# Set the full path for the final combined CSV file
combined_csv_path = os.path.join(base_dir, f"Point_data/Sampled/Combined_Sampled_Points_{start_year}-{end_year}.csv")

# Open the output file in write mode (this will create the file if it doesn't exist)
with open(combined_csv_path, 'w', newline='') as combined_file:
    writer = csv.writer(combined_file)  # Create a CSV writer object
    header_written = False  # Track whether the header (column names) has been written yet

    # Loop through the list of all monthly CSV paths previously generated
    for path in all_csv_paths:
        # Check that the file actually exists (some months may have been skipped)
        if os.path.exists(path):
            with open(path, 'r') as infile:
                reader = csv.reader(infile)  # Create a CSV reader for the current file
                header = next(reader)  # Read the first row as the header
                if not header_written:
                    writer.writerow(header)  # Write the header to the combined file only once
                    header_written = True
                for row in reader:
                    writer.writerow(row)  # Write each data row to the final CSV

# Log a message once everything is done
logging.info(f"All data processing complete. Combined CSV saved as 'Complete_Sampled_Data_{start_year}-{end_year}.csv'")
