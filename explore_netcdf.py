#!/usr/bin/env python3
"""
Script to explore NetCDF file structure for ARGO data
"""
import netCDF4 as nc
import os
import sys

def explore_netcdf_file(filepath):
    """Explore a NetCDF file and print its structure"""
    try:
        print(f"\n=== Exploring {filepath} ===")
        f = nc.Dataset(filepath, 'r')
        
        print("\nDimensions:")
        for dim in f.dimensions:
            print(f"  {dim}: {f.dimensions[dim].size}")
        
        print("\nVariables:")
        for var in f.variables:
            var_obj = f.variables[var]
            long_name = getattr(var_obj, 'long_name', '')
            units = getattr(var_obj, 'units', '')
            print(f"  {var}: {var_obj.shape} - {long_name} ({units})")
            
            # Show sample data for small variables
            if var_obj.size < 20 and var_obj.size > 0:
                try:
                    sample_data = var_obj[:]
                    print(f"    Sample data: {sample_data}")
                except:
                    print(f"    Sample data: [unable to read]")
        
        print("\nGlobal attributes:")
        for attr in f.ncattrs():
            print(f"  {attr}: {getattr(f, attr)}")
            
        f.close()
        return True
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

def main():
    # Explore a few NetCDF files
    netcdf_files = [
        'argo_data/1900022_meta.nc',
        'argo_data/D1900022_001.nc',
        'argo_data/R1900022_001.nc'
    ]
    
    for filepath in netcdf_files:
        if os.path.exists(filepath):
            explore_netcdf_file(filepath)
        else:
            print(f"File not found: {filepath}")
    
    # Also try to list all files and explore a few
    print("\n=== Available NetCDF files ===")
    argo_dir = 'argo_data'
    if os.path.exists(argo_dir):
        files = [f for f in os.listdir(argo_dir) if f.endswith('.nc')]
        print(f"Found {len(files)} NetCDF files")
        
        # Explore first few files
        for i, filename in enumerate(files[:3]):
            filepath = os.path.join(argo_dir, filename)
            print(f"\n--- File {i+1}: {filename} ---")
            explore_netcdf_file(filepath)

if __name__ == "__main__":
    main()
