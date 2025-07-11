# Import necessary libraries and modules
import processing  # QGIS processing framework
import sys, os
from datetime import datetime, timezone, timedelta
from qgis.analysis import QgsNativeAlgorithms  # QGIS built-in tools
from osgeo import gdal  # GDAL: Geospatial Data Abstraction Library
from processing.core.Processing import Processing
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsProcessingContext, 
    QgsProcessingFeedback, edit, QgsApplication, 
    QgsProcessingFeatureSourceDefinition, QgsRasterLayer,
    QgsRasterBandStats, QgsField, QgsFeature, QgsGeometry,
    QgsPointXY, QgsVectorFileWriter, 
    QgsCoordinateReferenceSystem, QgsProcessingProvider
)
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider


# === Initialize the QGIS processing environment ===
Processing.initialize()

# Add QGIS built-in tools and GDAL tools to the processing framework
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
QgsApplication.processingRegistry().addProvider(GdalAlgorithmProvider())

print("✅ GDAL Processing tools enabled.")


# === Load shapefile of all Canadian provinces ===
base_dir = 'C:/Users/tdoa2/OneDrive/Desktop/Data analytics/BCIT Data Analytics Certificate/BABI 9050/Code/Spatial data analysis/Spatial data cleaning' # Base directory for data
canada_provinces_path = os.path.join(base_dir, 'Map_of_Canada/lpr_000b16a_e.shp')  # Path to Canada shapefile
canada_layer = QgsVectorLayer(canada_provinces_path, 'Canada Provinces', 'ogr')  # Load as vector layer using OGR driver

# Check if the layer loaded successfully
if not canada_layer.isValid():
    print("❌ Canada provinces layer failed to load.")
else:
    print("✅ Canada provinces layer created.")


# === Extract just the British Columbia (BC) boundary from the Canada shapefile ===
bc_output_path = os.path.join(base_dir, 'Map_of_Canada/BC_boundary.shp')  # Output path for BC-only shapefile

# Use QGIS attribute filter tool to extract BC where province abbreviation (PREABBR) = 'B.C.'
processing.run("native:extractbyattribute", {
    'INPUT': canada_layer,
    'FIELD': 'PREABBR',
    'OPERATOR': 0,  # 0 = equals
    'VALUE': 'B.C.',
    'OUTPUT': bc_output_path
})
print("✅ BC boundary extracted and saved to:", bc_output_path)


# === Load the extracted BC boundary shapefile as a layer ===
bc_boundary_layer = QgsVectorLayer(bc_output_path, 'BC Boundary', 'ogr')
if bc_boundary_layer.isValid():
    print("✅ BC Boundary layer created.")
else:
    print("❌ Failed to load BC Boundary layer.")


# === Reproject the BC boundary to a new coordinate system (EPSG:3347 - NAD83 / BC Albers) ===
reprojected_bc_boundary = os.path.join(base_dir, 'Map_of_Canada/BC_boundary_epsg3347.shp')  # New output path

# Run the reprojection using QGIS processing tool
processing.run("native:reprojectlayer", {
    'INPUT': bc_output_path,
    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3347'),  # New coordinate reference system
    'OUTPUT': reprojected_bc_boundary
})
print("✅ Reprojected BC boundary to EPSG:3347")


# === Load the reprojected BC boundary and add it to the QGIS project ===
bc_boundary_layer_3347 = QgsVectorLayer(reprojected_bc_boundary, 'BC Boundary (EPSG:3347)', 'ogr')
if bc_boundary_layer_3347.isValid():
    QgsProject.instance().addMapLayer(bc_boundary_layer_3347)  # Add to current QGIS project
    print("✅ Reprojected BC boundary layer created successfully.")
else:
    print("❌ Failed to load reprojected BC boundary layer.")


# === Prepare to clip and reproject a fuel type raster to match the BC boundary ===
fuel_raster_path = os.path.join(base_dir, 'National_FBP_Fueltypes_version2014b/nat_fbpfuels_2014b.tif')  # Original raster
clipped_raster_temp = os.path.join(base_dir, 'National_FBP_Fueltypes_version2014b/temp_clipped_fuel.tif')  # Temp clipped raster
final_clipped_raster = os.path.join(base_dir, 'National_FBP_Fueltypes_version2014b/BC_fuel_type_epsg3347.tif')  # Final reprojected output


# === Clip the fuel raster to the reprojected BC boundary area ===
processing.run("gdal:cliprasterbymasklayer", {
    'INPUT': fuel_raster_path,  # Raster to be clipped
    'MASK': reprojected_bc_boundary,  # Mask to clip against (BC boundary)
    'SOURCE_CRS': None,
    'TARGET_CRS': None,
    'NODATA': -9999,  # Assign nodata value for areas outside the boundary
    'ALPHA_BAND': False,
    'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': True,
    'OPTIONS': '',
    'DATA_TYPE': 0,
    'EXTRA': '',
    'OUTPUT': clipped_raster_temp
})
print("✅ Temporary clipped fuel raster created.")


# === If the clipped raster exists, reproject it to match BC’s coordinate system ===
if os.path.exists(clipped_raster_temp):
    processing.run("gdal:warpreproject", {
        'INPUT': clipped_raster_temp,
        'SOURCE_CRS': None,
        'TARGET_CRS': 'EPSG:3347',  # Project to BC Albers CRS
        'RESAMPLING': 0,  # Use nearest neighbor resampling
        'NODATA': None,
        'TARGET_RESOLUTION': None,
        'OPTIONS': '',
        'DATA_TYPE': 0,
        'TARGET_EXTENT': None,
        'TARGET_EXTENT_CRS': None,
        'MULTITHREADING': False,
        'OUTPUT': final_clipped_raster
    })
    print("✅ Reprojected raster to EPSG:3347 successfully.")

    # Load the final raster and add it to the project if it is valid
    reprojected_layer = QgsRasterLayer(final_clipped_raster, "BC Fuel Type (EPSG:3347)")
    if reprojected_layer.isValid():
        print("✅ Reprojected raster added to project.")
        QgsProject.instance().addMapLayer(reprojected_layer)
    else:
        print("❌ Failed to load reprojected raster.")
else:
    print(f"❌ File not found: {clipped_raster_temp}")


# === PARAMETERS
start_year = 2000  # Start year for processing data
end_year = 2024    # End year for processing data (inclusive)

# --- Dictionary mapping month numbers to names
month_words = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}


# -- Get climate data function
def climate_extraction(year, month_name, month_num):
    # Define path where climate data for the specific year and month will be saved
    yearly_climate = os.path.join(base_dir, f"climate_data/GRIB_climate_data/{year}/{month_name}")
    os.makedirs(yearly_climate, exist_ok=True)

    # Handle GRIB file naming based on even/odd year pattern
    # GRIB files contain compressed climate data for two-year ranges
    if year % 2 == 0:
        climate_grib_path = os.path.join(base_dir, f"climate_data/GRIB_climate_data/{year}-{year + 1}.grib")
        bc_climate_temp = os.path.join(yearly_climate, f"BC_temp_{year}-{year + 1}_{month_name}.tif")
        bc_climate_final = os.path.join(yearly_climate, f"BC_{year}-{year + 1}_{month_name}.tif")
    else:
        climate_grib_path = os.path.join(base_dir, f"climate_data/GRIB_climate_data/{year - 1}-{year}.grib")
        bc_climate_temp = os.path.join(yearly_climate, f"BC_temp_{year - 1}-{year}_{month_name}.tif")
        bc_climate_final = os.path.join(yearly_climate, f"BC_{year - 1}-{year}_{month_name}.tif")

    # Open the GRIB file using GDAL
    ds = gdal.Open(climate_grib_path)
    if ds is None:
        print("❌ Could not open GRIB file.")
        return

    # Get total number of data bands (each band corresponds to a climate measurement at a time)
    band_count = ds.RasterCount
    print(f"📊 Total bands: {band_count}")

    # Initialize filter conditions
    target_year = year
    target_month = month_num
    selected_band_indices = []

    # Loop through all bands and extract those that match the target month/year
    for i in range(1, band_count + 1):
        band = ds.GetRasterBand(i)
        metadata = band.GetMetadata()
        valid = metadata.get("GRIB_VALID_TIME")
        comment = metadata.get("GRIB_COMMENT", "").lower()

        if valid:
            valid_dt = datetime.fromtimestamp(int(valid), tz=timezone.utc)
            adjusted_dt = valid_dt

            # Adjust date if the variable is a cumulative type (e.g., total precipitation)
            if any(keyword in comment for keyword in ["[m]", "precipitation", "total"]):
                adjusted_dt += timedelta(days=1)

            # Keep only bands from the desired month and year
            if adjusted_dt.year == target_year and adjusted_dt.month == target_month:
                selected_band_indices.append(i)
                print(f"🟢 Band {i} → {adjusted_dt.strftime('%Y-%m-%d')} (adjusted from {valid_dt.strftime('%Y-%m-%d')})")
            else:
                print(f"⚪️ Band {i} skipped → {adjusted_dt.strftime('%Y-%m-%d')}")
        else:
            print(f"⚠️ Band {i} has no VALID_TIME")

    # Stop if no bands match the selected month/year
    if not selected_band_indices:
        print(f"⚠️ No bands selected for {month_name} {year}. Skipping...")
        return

    print(f"\n📦 Bands selected for {target_year}-{target_month:02d}: {selected_band_indices}")

    # Step 1: Extract each selected band to an in-memory temporary file
    temp_band_files = []
    for i, band_index in enumerate(selected_band_indices):
        temp_path = f"/vsimem/temp_band_{i+1}.tif"
        gdal.Translate(temp_path, climate_grib_path, bandList=[band_index])
        temp_band_files.append(temp_path)

    # Step 2: Combine selected bands into a virtual raster (VRT)
    output_vrt = f"/vsimem/{month_name}_{year}.vrt"
    gdal.BuildVRT(output_vrt, temp_band_files, separate=True)

    # Step 3: Convert the virtual raster to a physical GeoTIFF file
    output_tif = os.path.join(yearly_climate, f"{month_name}_{year}.tif")
    gdal.Translate(output_tif, output_vrt)

    # Step 4: Clip the raster to the BC boundary using QGIS
    processing.run("gdal:cliprasterbymasklayer", {
        'INPUT': output_tif,
        'MASK': bc_boundary_layer_3347,  # Mask is the BC polygon boundary
        'SOURCE_CRS': None,
        'TARGET_CRS': None,
        'NODATA': -9999,
        'ALPHA_BAND': False,
        'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': True,
        'OPTIONS': '',
        'DATA_TYPE': 0,
        'EXTRA': '',
        'OUTPUT': bc_climate_temp
    })

    # Step 5: Reproject clipped raster to EPSG:3347 (Albers Equal Area projection used for Canada)
    if os.path.exists(bc_climate_temp):
        processing.run("gdal:warpreproject", {
            'INPUT': bc_climate_temp,
            'SOURCE_CRS': None,
            'TARGET_CRS': 'EPSG:3347',
            'RESAMPLING': 0,
            'NODATA': None,
            'TARGET_RESOLUTION': None,
            'OPTIONS': '',
            'DATA_TYPE': 0,
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'MULTITHREADING': False,
            'OUTPUT': bc_climate_final
        })
        print("✅ Reprojected raster to EPSG:3347 successfully.")
        bc_climate_raster_epsg3347 = QgsRasterLayer(bc_climate_final, f"BC Climate raster {month_name} {year} (EPSG:3347)")
    else:
        print("❌ Failed to reproject raster to EPSG:3347.")
        return

    # Step 6: Load the reprojected climate raster into QGIS
    if bc_climate_raster_epsg3347.isValid():
        print("✅ Loaded reprojected climate raster successfully.")
    else:
        print("❌ Failed to load reprojected raster.") 

    # === Prepare folder for storing filled raster bands ===
    output_folder = os.path.join(yearly_climate, f"Filled_Bands_{month_name}_{year}")
    bc_climate_filled = os.path.join(output_folder, 'Filled_Stacked_Climate.tif')
    os.makedirs(output_folder, exist_ok=True)

    # === Step 7: Fill in NoData (missing pixel) values for each band ===
    ds_final = gdal.Open(bc_climate_final)
    if ds_final is None:
        print(f"❌ Failed to open reprojected raster {bc_climate_final}")
        return

    band_count = ds_final.RasterCount
    print(f"📊 Found {band_count} bands to fill.")

    filled_band_paths = []

    for i in range(1, band_count + 1):
        output_band = os.path.join(output_folder, f'filled_band_{i}.tif')
        print(f"🌀 Filling NoData for Band {i}...")

        processing.run("gdal:fillnodata", {
            'INPUT': bc_climate_final,
            'BAND': i,
            'MASK_LAYER': None,
            'DISTANCE': 10,
            'ITERATIONS': 0,
            'NO_MASK': False,
            'OUTPUT': output_band
        })

        if os.path.exists(output_band):
            print(f"✅ Band {i} filled and saved to {output_band}")
            filled_band_paths.append(output_band)
        else:
            print(f"❌ Failed to process Band {i}")

    # === Step 8: Stack filled bands into one multi-band raster file ===
    print("🧱 Stacking filled bands into one raster...")
    vrt_path = os.path.join(output_folder, 'temp_stack.vrt')
    gdal.BuildVRT(vrt_path, filled_band_paths, separate=True)
    gdal.Translate(bc_climate_filled, vrt_path)

    print(f"🎉 All bands filled and stacked! Final output: {bc_climate_filled}")

    # Load final stacked raster into QGIS
    layer_name = f"Filled BC Climate {month_name} {year}"
    bc_climate_layer = QgsRasterLayer(bc_climate_filled, layer_name)
    if bc_climate_layer.isValid():
        print(f"✅ Reprojected climate raster '{layer_name}' created successfully.")
    else:
        print("❌ Failed to load reprojected raster.")

    # === Cleanup temporary in-memory files ===
    gdal.Unlink(output_vrt)
    for path in temp_band_files:
        gdal.Unlink(path)

    return bc_climate_filled
    

for year in range(start_year, end_year + 1):
    # Loop through each year in the specified range (e.g., from 2000 to 2024)
    print(f"Processing {year}...")

    # Loop through each month of the year using the month_words dictionary
    for month_num, month_name in month_words.items():
        # For the current month and year, extract and process climate data
        # This function finds the correct GRIB bands, clips to BC, reprojects, fills nodata, and stacks them
        bc_climate_filled = climate_extraction(year, month_name, month_num)
