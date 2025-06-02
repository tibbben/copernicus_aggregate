# example script from data request page
import cdsapi
from netCDF4 import Dataset
import os
import json
import sys

def copernicus_aggregate(opts):
    data_format = "grib" if opts['format'] == "grib" else "netcdf"
    dataset = "reanalysis-era5-single-levels"
    request = {
        "product_type": ["reanalysis"],
        "variable": [opts['variable']],
        "year": [opts['year']],
        "month": [
            "01", "02", "03",
            "04", "05", "06",
            "07", "08", "09",
            "10", "11", "12"
        ],
        "day": [
            "01", "02", "03",
            "04", "05", "06",
            "07", "08", "09",
            "10", "11", "12",
            "13", "14", "15",
            "16", "17", "18",
            "19", "20", "21",
            "22", "23", "24",
            "25", "26", "27",
            "28", "29", "30",
            "31"
        ],
        "time": [
            "00:00", "01:00", "02:00",
            "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00",
            "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00",
            "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00",
            "21:00", "22:00", "23:00"
        ],
        "data_format": data_format,
        "download_format": opts['extension'],
        "area": opts['extent']
    }
    target = f"{opts['table']}.{opts['extension']}"

    print(request)
    print(dataset)
    print(target)
    
    client = cdsapi.Client()
    client.retrieve(dataset, request, target)

    if opts['extension'] == "zip":
        cmd = (
            f"unzip {opts['table']}.{opts['extension']}\n"
            f"mv data_stream-oper_stepType-instant.{opts['format']} temp_{opts['table']}.{opts['format']}"
        )
        res = os.system(cmd)
        print(res)

    # Load download and average across all time bands 
    # assumes file is netcdf
    nc_f = f"./temp_{opts['table']}.{opts['format']}"  # Your filename
    nc_fid = Dataset(nc_f, 'r')
    variable = nc_fid.variables[opts['bands'][0]][:]  # shape is time, lat, lon
    latitude = nc_fid.variables['latitude'][:]
    longitude = nc_fid.variables['longitude'][:]
    avg_variable = variable.mean(axis=0)

    # Create NetCDF file
    ncfile = Dataset(f"{opts['table']}.{opts['format']}", 'w', format='NETCDF4')
    ncfile.Conventions = "CF-1.7"
    ncfile.geo_crs = "EPSG:4326"

    # Create dimensions
    lat = ncfile.createDimension('latitude', avg_variable.shape[0])
    lon = ncfile.createDimension('longitude', avg_variable.shape[1])
    
    # Create variables
    lat = ncfile.createVariable('latitude', 'f8', ('latitude',))
    lat.units = 'degrees_north'
    lat.standard_name = 'latitude'
    lon = ncfile.createVariable('longitude', 'f8', ('longitude',))
    lon.units = 'degrees_east'
    lon.standard_name = 'longitude'
    var= ncfile.createVariable(opts['variable'], 'f8', ('latitude', 'longitude'))
    var.grid_mapping = 'crs'
    var.units = opts['units']
    
    # create CRS var
    crs_var = ncfile.createVariable('crs', 'i8', ())
    crs_var.standard_name = 'crs'
    crs_var.grid_mapping_name = 'latitude_longitude'
    crs_var.crs_wkt = ("GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',"
                       "SPHEROID['WGS_1984',6378137.0,298.257223563]],"
                       "PRIMEM['Greenwich',0.0],"
                       "UNIT['Degree',0.0174532925199433]]")
    
    # Write data
    lat[:] = latitude
    lon[:] = longitude
    var[:] = avg_variable
    
    # Close file
    ncfile.close()

def main():
    if len(sys.argv) == 3:
        opts=json.loads(sys.argv[1])
        opts['extent'] = [opts['extent'][3]] + opts['extent'][0:3]
        opts['variable'] = opts['attributes'][0].split(';')[0]
        opts['units'] = opts['attributes'][0].split(';')[4]
        opts['year'] = sys.argv[2]
    else: # testing default
        opts = {
            "table": "tz_1984_copernics_avg_temp",
            "extension": "zip",
            "year": "1984",
            "extent": [-0.8, 29, -12, 41],
            "variable": "2m_temperature",
            "units": "kelvin",
            "bands": ["t2m"],
            "format": "nc"
        }
    copernicus_aggregate(opts)

if __name__ == "__main__":
    main()