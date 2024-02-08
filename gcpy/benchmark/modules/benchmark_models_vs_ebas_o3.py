#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gcpy/benchmark/modules/benchmark_model_vs_obs.py

Python functions to plot modeled data from 1-year fullchem benchmark
simulations against observations for the year 2019.  At present, only
O3 plots are supported, but this can be extended in the future.

Author: Matt Rowlinson <matthew.rowlinson@york.ac.uk>

Linted with PyLint and incorporated into GCPy
by Bob Yantosca <yantosca@seas.harvard.edu>
"""
import glob
from datetime import datetime, timedelta
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import xarray as xr
from gcpy.constants import skip_these_vars
from gcpy.util import verify_variable_type, dataset_reader, make_directory
from gcpy.cstools import extract_grid
from gcpy.grid import get_nearest_model_data
from gcpy.benchmark.modules.benchmark_utils import get_geoschem_level_metadata


def read_nas(
        input_file,
        verbose=False,

):
    """
    Read NASA Ames data files from EBAS (https://ebas-data.nilu.no)
    Creates data frame of O3 values converted to ppb and dictionary
    with key site information (name, lat, lon, altitude)

    Args:
    -----
    input_file : str
        Path to data file with observational data (e.g. sonde data).
    Keyword Args:
    -------------
    verbose : bool
        Toggles verbose printout on (True) or off (False).
        Default value: False

    Returns:
    --------
    obs_dataframe : pandas.DataFrame
        Dataframe containing observational data from input_file.
    obs_site_coords : dict
        Dictionary containing formatted site name: lon, lat and altitude.
    """
    verify_variable_type(input_file, str)

    if verbose:
        print(f"read_nas: Reading {input_file}")

    with open(input_file, encoding='UTF-8') as the_file:
        header = np.array(
            [next(the_file) for x in range(155) ]
        )
        n_hdr = int(
            header[0].split(' ')[0]
        )
        st_ymd = header[6].split(' ')
        st_ymd = list(
            filter(
                None,
                st_ymd
            )
        )
        start_date = datetime(
            int(st_ymd[0]),
            int(st_ymd[1]),
            int(st_ymd[2])
        )
        for line in header:
            if 'Station name' in line:
                site = line.split(':')[1:]
                site = '_'.join(site).replace('\n','').\
                    replace('  ',' ').replace('/','-')
                site = site.replace('Atmospheric Observatory','')
                site = site.replace(' Research Station','')
            elif 'Station longitude:' in line:
                lon = float(line.split(' ')[-1].replace('\n',''))
            elif 'Station latitude:' in line:
                lat = float(line.split(' ')[-1].replace('\n',''))
            elif 'Station altitude:' in line:
                alt = float(line.split(' ')[-2].replace('\n',''))

    file_hdr = np.loadtxt(
        input_file,
        skiprows=n_hdr
    )
    obs_dataframe = pd.DataFrame(
        file_hdr,
        index=file_hdr[:,0]
    )
    obs_dataframe, qcflag = find_times(
        obs_dataframe,
        start_date
    )
    obs_dataframe = pd.DataFrame(
        {
            'Value': obs_dataframe.values/1.99532748,
            'Flag': qcflag
        },
        index=obs_dataframe.index
    )
    obs_dataframe = obs_dataframe[obs_dataframe.Flag == 0.000]
    obs_dataframe = obs_dataframe.loc['2019']
    obs_dataframe = obs_dataframe.resample('H').mean()
    obs_dataframe = pd.DataFrame(
        {
            site: obs_dataframe.Value
        },
        index=obs_dataframe.index
    )
    obs_site_coords = { site:
          {
              'lon': lon,
              'lat': lat,
              'alt': alt
          }
    }

    return obs_dataframe, obs_site_coords


def read_observational_data(
        path,
        verbose
):
    """
    Reads the observational O3 data from EBAS
    (taken from https://ebas-data.nilu.no/ on 15/05/2023)

    Loops over all data files (in NASA/Ames format) within
    a folder and concatenates them into a single DataFrame.

    Args:
    -----
    path : str
        Path to the observational data directory
    verbose : bool
        Toggles verbose printout on (True) or off (False).
        Default value: False

    Returns:
    --------
    obs_dataframe : pandas.DataFrame
        DataFrame object with the observational data (i.e. station
        names, data, metadata).
    obs_site_coords : dict
        Dictionary with coordinates of each observation site
    """
    verify_variable_type(path, str)

    first = True
    obs_site_coords = {}
    dataframe = None
    for infile in sorted(glob.glob(f"{path}/*nas")):
        obs_dataframe, xyz = read_nas(
            infile,
            verbose=verbose
        )
        if first:
            dataframe = obs_dataframe
            obs_site_coords.update(xyz)
            first = False
        else:
            dataframe = pd.concat(
                [dataframe, obs_dataframe],
                axis=1
            )
            obs_site_coords.update(xyz)

    # If dataframe0 is undefined, the loop didn't execute... so throw error
    if dataframe is None:
        raise ValueError(f"Could not find data in {path}!")

    obs_dataframe = dataframe.groupby(
        dataframe.columns,
        axis=1
    ).max()

    return obs_dataframe, obs_site_coords


def read_model_data(
        filepaths,
        varname,
        verbose=False,
):
    """
    Reads model data from a netCDF file.  Adds special handling to look
    for species concentrations variable names starting with either
    "SpeciesConcVV" or "SpeciesConc".  This is necessary for backwards
    compatitbility with GEOS-Chem output prior to version 14.1.0.

    Args:
    -----
    filepaths : list of str
        List of data files to read.
    varname : str or list of str
        Variable name(s) to read from data files.

    Keyword Args:
    -------------
    varbose : bool
        Toggles verbose output on (True) or off (False).
        Default value: False

    Returns:
    --------
    dataarray : xarray.DataArray
        DataArray object containing data read from files
        specified by the filepaths argument.
    """

    # Read the Ref and Dev model data
    reader = dataset_reader(
        multi_files=True,
        verbose=verbose,
    )

    # Set temporary variable name for use below
    varname_tmp = varname

    # First try reading the data as-is
    try:
        dataset = reader(
            filepaths,
            drop_variables=skip_these_vars,
            data_vars=[varname_tmp]
        ).load()

    # If we encounter a ValueError, it may be because the data is
    # older # and may have e.g. SpeciesConc fields instead of
    # SpeciesConcVV fields.  Reset the varname_tmp and try again.
    except ValueError:
        varname_tmp = varname_tmp.replace("VV", "")
        dataset = reader(
            filepaths,
            drop_variables=skip_these_vars,
            data_vars=[varname_tmp]
        ).load()

        # Rename to the original name to avid confusion with data
        # from GEOS-Chem versions prior to 14.1.0
        with xr.set_options(keep_attrs=True):
            dataset = dataset.rename({varname_tmp: varname})

    # If we fail again, then throw an error!
    except [FileNotFoundError, OSError, IOError] as exc:
        msg = f"get_model_data: Could not read Ref data for {varname}!"
        raise exc(msg) from exc

    # Create a DataArray object and convert to ppbv (if necessary)
    with xr.set_options(keep_attrs=True):
        dataarray = dataset[varname]
        if "mol mol-1" in dataarray.attrs["units"]:
            dataarray.values *= 1.0e9
            dataarray.attrs["units"] = "ppbv"

    return dataarray


def find_times(
        obs_dataframe,
        start_time
):
    """
    Convert timestamps in nasa ames data files to python datetime
    objects and set DataFrame index to the new datetime array.

    Args:
    ----------
    obs_dataframe : pandas.DataFrame
        DataFrame with O3 values from GAW site
    start_time : str
        Reference start time for timestamp taken from nasa ames file

    Returns
    ------
    obs_dataframe: pandas.DataFrame
        O3 in ppbV with datetime index
    qcflag : pandas.Dataframe
        QC flag with datetime index
    """
    end_time = obs_dataframe[obs_dataframe.columns[1]]
    time_x = []

    for index in range(len(end_time)):
        time_x.append(start_time + timedelta(days=end_time.values[index]))

    obs_dataframe.index = time_x
    qcflag =obs_dataframe[obs_dataframe.columns[-1]]
    obs_dataframe = obs_dataframe[obs_dataframe.columns[2]]

    return obs_dataframe, qcflag


def get_nearest_model_data_to_obs(
        gc_data,
        gc_levels,
        lon_value,
        lat_value,
        alt_value,
        gc_cs_grid=None

):
    """
    Returns GEOS-Chem model data (on a cubed-sphere grid) at the
    grid box closest to an observation site location.

    Args:
    -----
    gc_data : xarray.DataSet
        GEOS-Chem output to be processed
    gc_levels: pandas.DataFrame
        Altitudes of GEOS-Chem levels in meters
    lon_value : float
        GAW site longitude
    lat_value : float
        GAW site latitude
    alt_value : float
        GAW site altitude

    Keyword Args: (Optional)
    ------------------------
    gc_cs_grid : xarray.Dataset or NoneType
        Dictionary containing the cubed-sphere grid definition
        (or None if gc_data is not placed on a cubed-sphere grid).

    Returns:
    --------
    dataframe: pandas.DataFrame
        Model data closest to the observation site.
    """
    verify_variable_type(gc_data, xr.DataArray)
    verify_variable_type(gc_cs_grid, (xr.Dataset, type(None)))
    verify_variable_type(gc_levels, pd.DataFrame)

    # Prevent the latitude from getting too close to the N or S poles
    lat_value = max(min(lat_value, 89.75), -89.75)

    # Nearest GEOS-Chem data to (lat, lon) of observation
    dframe = get_nearest_model_data(
        gc_data,
        lon_value,
        lat_value,
        gc_cs_grid=gc_cs_grid
    )
    dframe = dframe.reset_index()

    # Nearest GEOS-Chem level to observation
    gc_alts = gc_levels["Altitude (m)"].values
    n_alts = len(gc_alts)
    z_idx =(np.abs(gc_alts - float(alt_value))).argmin()

    # Pick out elements of the dataframe at the nearest level to obs
    rows = np.zeros(len(dframe), dtype=bool)
    good = [(v * n_alts) + z_idx for v in range(12)]
    rows[good] = True

    return dframe[rows].set_index("time")


def prepare_data_for_plot(
        obs_dataframe,
        obs_site_coords,
        obs_site_name,
        ref_dataarray,
        ref_cs_grid,
        dev_dataarray,
        dev_cs_grid,
        gc_levels,
        varname="SpeciesConcVV_O3",
):
    """
    Prepares data for passing to routine plot_single_frames as follows:

    (1) Computes the mean of observations at the given station site.
    (2) Returns the GEOS-Chem Ref and Dev data at the gridbox closest
         to the given station site.
    (3) Creates the top-of-plot title for the given station site.

    Args:
    -----
    obs_dataframe : pandas.DataFrame
        Observations at each station site.
    obs_site_coords : dict
        Coordinates (lon, lat, alt) for each observation station site.
    obs_site_name : str
        Name of the observation station site.
    ref_dataarray, dev_dataarray : xarray.DataArray
        Data from the Ref and Dev model versions.
    ref_cs_grid, dev_cs_grid : xarray.Dataset or NoneType
        Dictionary containing the cubed-sphere grid definitions for
        ref_dataarray and dev_dataarray (or None if ref_dataarray or
        dev_dataarray are not placed on a cubed-sphere grid).
    gc_level_alts_m : pandas Series
        Metadata pertaining to GEOS-Chem vertical levels

    Keyword Args (Optional)
    -----------------------
    varname : str
        GEOS-Chem diagnostic name for the Ref and Dev model data.
        Default value: "SpeciesConcVV_O3"

    Returns:
    --------
    obs_dataframe : pandas.DataFrame
        Meanb observational data at the given station site.
    ref_series, dev_series : pandas Series
        Data from the Ref and Dev model versions at the
        closest grid box to the observation station site.
    subplot_title : str
        Plot title string for the given observation station site.
    subplot_ylabel : str
        Label for the Y-axis (e.g. species name).
    """
    verify_variable_type(obs_dataframe, pd.DataFrame)
    verify_variable_type(obs_site_coords, dict)
    verify_variable_type(obs_site_name, str)
    verify_variable_type(ref_dataarray, xr.DataArray)
    verify_variable_type(dev_dataarray, xr.DataArray)
    verify_variable_type(ref_cs_grid, (xr.Dataset, type(None)))
    verify_variable_type(dev_cs_grid, (xr.Dataset, type(None)))
    verify_variable_type(gc_levels, pd.DataFrame)
    verify_variable_type(varname, str)

    # Get data from the Ref model closest to the data site
    coords = [
        round(obs_site_coords[obs_site_name]['lon'], 2),
        round(obs_site_coords[obs_site_name]['lat'], 2),
        round(obs_site_coords[obs_site_name]['alt'], 1)
    ]

    # Get data from the Ref model closest to the obs site
    ref_dataframe = get_nearest_model_data_to_obs(
        ref_dataarray,
        gc_levels,
        coords[0],                 # Obs site lon
        coords[1],                 # Obs site lat
        coords[2],                 # Obs site alt
        gc_cs_grid=ref_cs_grid
    )

    # Get data from the Dev model closest to the obs site
    dev_dataframe = get_nearest_model_data_to_obs(
        dev_dataarray,
        gc_levels,
        coords[0],                 # Obs site lon
        coords[1],                 # Obs site lat
        coords[2],                 # Obs site alt
        gc_cs_grid=dev_cs_grid,
    )

    # Take the monthly mean of observations for plotting
    # (since some observation sites have multiple months of data)
    obs_dataframe = obs_dataframe.resample('M').mean()

    # Create the top title for the subplot for this observation site
    # (use integer lon & lat values and N/S lat and E/W lon notation)
    lon = int(round(obs_site_coords[obs_site_name]['lon'], 0))
    lat = int(round(obs_site_coords[obs_site_name]['lat'], 0))
    ystr = "S"
    if lat >= 0:
        ystr = "N"
    xstr = "W"
    if lon >= 0:
        xstr = "E"
    lon = abs(lon)
    lat = abs(lat)
    subplot_title = \
        f"{obs_site_name.strip()} ({lat}$^\\circ${ystr},{lon}$^\\circ${xstr})"

    # Y-axis label (i.e. species name)
    subplot_ylabel = varname.split("_")[1] + " (ppbv)"

    return obs_dataframe, ref_dataframe[varname], dev_dataframe[varname], \
        subplot_title, subplot_ylabel


def plot_single_station(
        fig,
        rows_per_page,
        cols_per_page,
        subplot_index,
        subplot_title,
        subplot_ylabel,
        obs_dataframe,
        obs_site_name,
        ref_series,
        ref_label,
        dev_series,
        dev_label
):
    """
    Plots observation data vs. model data at a single station site.

    Args:
    -----
    fig : matplotlib.figure.Figure
        Matplotlib Figure object containing the plot.
    rows_per_page, cols_per_page : int
        Number of rows and columns on each page of the plot.
    subplot_index : int
        Index of the subplot on the page.  Runs from 0 to
        (cols_per_page * rows_per_page - 1).
    subplot_title, subplot_ylabel : str
        Top title and y-axis label for each subplot
    obs_dataframe : pandas.DataFrame
        Observational data.
    obs_site_name: : str
        Name of the observation station site.
    ref_series, dev_series : pandas Series
        GEOS-Chem data at closest grid box to the observation
        station site for the Ref and Dev model versions.
    ref_label, dev_label : str
        Descriptive labels (e.g. version numbers) for the
        GEOS-Chem Ref and Dev model versions.
    """
    verify_variable_type(fig, Figure)
    verify_variable_type(rows_per_page, int)
    verify_variable_type(cols_per_page, int)
    verify_variable_type(subplot_index, int)
    verify_variable_type(subplot_title, str)
    verify_variable_type(subplot_ylabel, str)
    verify_variable_type(obs_dataframe, pd.DataFrame)
    verify_variable_type(ref_series, pd.Series)
    verify_variable_type(ref_label, str)
    verify_variable_type(dev_series, pd.Series)
    verify_variable_type(dev_label, str)

    # Create matplotlib axes object for this subplot
    # axes_subplot is of type matplotlib.axes_.subplots.AxesSubplot
    axes_subplot = fig.add_subplot(
        rows_per_page,
        cols_per_page,
        subplot_index + 1,
    )

    # Set title for top of each frame
    axes_subplot.set_title(
        f"{subplot_title}",
        weight='bold',
        fontsize=7
        )

    ## Plot observational data
    axes_subplot.plot(
        obs_dataframe.index,
        obs_dataframe[obs_site_name],
        color='k',
        marker='^',
        markersize=4,
        lw=1,
        label='Surface O3 (EBAS, 2019)'
    )

    # Plot model data
    axes_subplot.plot(
        obs_dataframe.index,
        ref_series,
        color='r',
        marker='o',
        markersize=3,
        lw=1,
        label=ref_label
    )
    axes_subplot.plot(
        obs_dataframe.index,
        dev_series,
        color='g',
        marker='s',
        markersize=3,
        lw=1,
        label=dev_label
    )

    # Apply y-axis label only if this is a leftmost plot panel
    if subplot_index == 0 or subplot_index % cols_per_page == 0:
        axes_subplot.set_ylabel(
            subplot_ylabel,
            fontsize=8
        )

    # Set X-axis and Y-axis ticks and labels
    axes_subplot.set_xticks(
        obs_dataframe.index
    )
    # NOTE: In newer versions of matplotlib you can pass the
    # xticklabels keyword to the set_xticks function.  But we need
    # to set the xticklabels separately for backwards compatibility
    # with older matplotlib versions. -- Bob Yantosca (06 Jul 2023)
    axes_subplot.set_xticklabels(
        ['J','F','M','A','M','J','J','A','S','O','N','D']
    )
    axes_subplot.set_ylim(
        0,
        80
    )
    axes_subplot.set_yticks(
        [0, 20, 40, 60, 80]
    )
    axes_subplot.tick_params(
        axis='both',
        which='major',
        labelsize=6
    )


def plot_one_page(
        pdf,
        obs_dataframe,
        obs_site_coords,
        obs_site_names,
        ref_dataarray,
        ref_label,
        ref_cs_grid,
        dev_dataarray,
        dev_label,
        dev_cs_grid,
        gc_levels,
        rows_per_page=3,
        cols_per_page=3,
        varname="SpeciesConcVV_O3",
):
    """
    Plots a single page of models vs. observations.

    Args:
    -----
    obs_dataframe : pandas.DataFrame
        Observations at each station site.
    obs_site_coords : dict
        Coordinates (lon, lat, alt) for each observation station site.
    obs_site_names : list of str
        Names of observation station sites that fit onto a single page.
    ref_dataarray, dev_dataarray : xarray.DataArray
        Data from the Ref and Dev model versions.
    ref_label, dev_label: str
        Labels describing the Ref and Dev datasets (e.g. version numbers)
    ref_cs_grid, dev_cs_grid : xarray.Dataset or NoneType
        Dictionary containing the cubed-sphere grid definitions for
        ref_dataarray and dev_dataarray (or None if ref_dataarray or
        dev_dataarray are not placed on a cubed-sphere grid).
    gc_levels : pandas.DataFrame
        Metadata pertaining to GEOS-Chem vertical levels

    Keyword Args:
    -------------
    rows_per_page, cols_per_page : int
        Number of rows and columns to plot on a single page.
        Default values: 3 rows, 3 columns
    varname : str
        Variable name for GEOS-Chem diagnostic data.
        Default value: "SpeciesConcVV_O3"
    verbose : bool
        Toggles verbose printout on (True) or off (False).
        Default value: False
    """
    verify_variable_type(obs_dataframe, pd.DataFrame)
    verify_variable_type(obs_site_coords, dict)
    verify_variable_type(obs_site_names, list)
    verify_variable_type(ref_dataarray, xr.DataArray)
    verify_variable_type(ref_label, str)
    verify_variable_type(ref_cs_grid, (xr.Dataset, type(None)))
    verify_variable_type(dev_dataarray, xr.DataArray)
    verify_variable_type(dev_label, str)
    verify_variable_type(dev_cs_grid, (xr.Dataset, type(None)))
    verify_variable_type(gc_levels, pd.DataFrame)

    # Define a new matplotlib.figure.Figure object for this page
    # Landscape width: 11" x 8"
    fig = plt.figure(figsize=(11, 8))
    fig.tight_layout()

    # Loop over all of the stations that fit on the page
    for subplot_index, obs_site_name in enumerate(obs_site_names):

        # Find the model Ref & Dev data closest to the observational
        # station site.  Also take monthly average of observations,
        obs_dataframe, \
        ref_series, dev_series, \
        subplot_title, subplot_ylabel \
        = prepare_data_for_plot(
            obs_dataframe,                # pandas.DataFrame
            obs_site_coords,              # dict
            obs_site_name,                # str
            ref_dataarray,                # xarray.DataArray
            ref_cs_grid,                  # dict or none
            dev_dataarray,                # xarray.DataArray
            dev_cs_grid,                  # dict or none
            gc_levels,                    # pandas.DataFrame
            varname=varname               # str
        )

        # Plot models vs. observation for a single station site
        plot_single_station(
            fig,                          # matplotlib.figure.Figure
            rows_per_page,                # int
            cols_per_page,                # int
            subplot_index,                # int
            subplot_title,                # str
            subplot_ylabel,               # str
            obs_dataframe,                # pandas.Dataframe
            obs_site_name,                # str
            ref_series,                   # pandas.Series
            ref_label,                    # str
            dev_series,                   # pandas.Series
            dev_label,                    # str
        )

    # Add extra spacing around plots
    plt.subplots_adjust(
        hspace=0.4,
        top=0.9
    )

    # Add top-of-page legend
    plt.legend(
        ncol=3,
        bbox_to_anchor=(0.5, 0.98),
        bbox_transform=fig.transFigure,
        loc='upper center'
    )

    # Save this page to the PDF file
    pdf.savefig(fig)


def plot_models_vs_obs(
        obs_dataframe,
        obs_site_coords,
        ref_dataarray,
        ref_label,
        dev_dataarray,
        dev_label,
        gc_levels,
        varname="SpeciesConcVV_O3",
        dst="./benchmark",
        **kwargs
):
    """
    Plots models vs. observations using a 3 rows x 3 column layout.

    Args:
    -----
    obs_dataframe : pandas.DataFrame
        Observations at each station site.
    obs_site_coords : dict
        Coordinates (lon, lat, alt) for each observation station site.
    ref_dataarray, dev_dataarray : xarray.DataArray
        Data from the Ref and Dev model versions.
    ref_label, dev_label: str
        Labels describing the Ref and Dev datasets (e.g. version numbers)
    gc_levels : pandas.DataFrame
        Metadata pertaining to GEOS-Chem vertical levels

    Keyword Args:
    -------------
    varname : str
        Variable name for GEOS-Chem diagnostic data.
        Default value: "SpeciesConcVV_O3"
    dst : str
        Root folder where output will be created.
        Default value: "./benchmark"
    verbose : bool
        Toggles verbose printout on (True) or off (False).
        Default value: False
    """
    verify_variable_type(obs_dataframe, pd.DataFrame)
    verify_variable_type(obs_site_coords, dict)
    verify_variable_type(ref_dataarray, xr.DataArray)
    verify_variable_type(ref_label, str)
    verify_variable_type(dev_dataarray, xr.DataArray)
    verify_variable_type(dev_label, str)
    verify_variable_type(gc_levels, pd.DataFrame)

    # Get the cubed-sphere grid definitions for Ref & Dev
    # (will be returned as "None" for lat/lon grids)
    ref_cs_grid = extract_grid(ref_dataarray)
    dev_cs_grid = extract_grid(dev_dataarray)

    # Figure setup
    plt.style.use("seaborn-v0_8-darkgrid")
    rows_per_page = 3
    cols_per_page = 3
    plots_per_page = rows_per_page * cols_per_page

    # Open the plot as a PDF document
    pdf_file = f"{dst}/models_vs_obs.surface.{varname.split('_')[1]}.pdf"
    pdf = PdfPages(pdf_file)

    # Sort station sites N to S latitude order according to:
    # https://www.geeksforgeeks.org/python-sort-nested-dictionary-by-key/
    # NOTE: obs_site_names will be a MultiIndex list (a list of tuples)
    obs_site_names = sorted(
        obs_site_coords.items(),
        key = lambda x: x[1]['lat'],
        reverse=True
    )

    # Convert obs_site_names from a MultiIndex list to a regular list
    obs_site_names = [list(tpl)[0] for tpl in obs_site_names]

    # Loop over the number of obs sites that fit on a page
    for start in range(0, len(obs_site_names), plots_per_page):
        end = start + plots_per_page - 1

        # Plot obs sites that fit on a single page
        plot_one_page(
            pdf,                          # PdfPages
            obs_dataframe,                # pandas.DataFrame
            obs_site_coords,              # dict
            obs_site_names[start:end+1],  # list of str
            ref_dataarray,                # xarray.DataArray
            ref_label,                    # str
            ref_cs_grid,                  # xarray.DataSet or NoneType
            dev_dataarray,                # xarray.DataArray
            dev_label,                    # str
            dev_cs_grid,                  # xarray.Dataset or NoneType
            gc_levels,                    # pandas.DataFrame
            rows_per_page=rows_per_page,  # int
            cols_per_page=cols_per_page,  # int
            varname=varname,              # str
        )

    # Close the PDF file after all pages are plotted.
    pdf.close()

    # Reset the plot style (this prevents the seaborn style from
    # being applied to other model vs. obs plotting scripts)
    plt.style.use("default")


def make_benchmark_models_vs_ebas_o3_plots(
        obs_filepaths,
        ref_filepaths,
        ref_label,
        dev_filepaths,
        dev_label,
        varname="SpeciesConcVV_O3",
        dst="./benchmark",
        verbose=False,
        overwrite=False
):
    """
    Driver routine to create model vs. observation plots.

    Args:
    -----
    obs_filepaths : str or list
        Path(s) to the observational data.
    ref_filepaths, dev_filepaths: str or list
        Path(s) to the Ref and Dev model versions to be compared.
    ref_label, dev_label : str
        Descriptive labels (e.g. for version numbers) for the
        Ref and Dev model data.

    Keyword Args (optional):
    ------------------------
    varname : str
        Variable name for model data to be plotted against
        observations.  Default value: "SpeciesConcVV_O3".
    dst : str
        Path to the root folder where plots will be created.
    verbose : bool
        Toggles verbose printout on (True) or off (False).
        Default value: False
    overwrite : bool
        Toggles whether plots should be overwritten (True)
        or not (False). Default value: True
    """
    verify_variable_type(obs_filepaths, (str, list))
    verify_variable_type(ref_filepaths, (str, list))
    verify_variable_type(ref_label, str)
    verify_variable_type(dev_filepaths, (str, list))
    verify_variable_type(dev_label, str)

    # Create the destination folder
    make_directory(
        dst,
        overwrite=overwrite
    )

    # Get GEOS-Chem level metadata
    gc_levels = get_geoschem_level_metadata(
        search_key=["Altitude (km)", "Eta Mid"]
    )
    gc_levels["Altitude (m)"] = gc_levels["Altitude (km)"] * 1000.0

    # Read the observational data
    obs_dataframe, obs_site_coords = read_observational_data(
        obs_filepaths,
        verbose=verbose
    )

    # Read the model data
    ref_dataarray = read_model_data(
        ref_filepaths,
        varname=varname
    )
    dev_dataarray = read_model_data(
        dev_filepaths,
        varname=varname
    )

    # Plot data vs observations
    plot_models_vs_obs(
        obs_dataframe,                    # pandas.DataFrame
        obs_site_coords,                  # dict
        ref_dataarray,                    # xarray.DataArray
        ref_label,                        # str
        dev_dataarray,                    # xarray.DataArray
        dev_label,                        # str
        gc_levels,                        # pandas.DataFrame
        varname=varname,                  # str
        dst=dst,                          # str
        verbose=verbose                   # bool
    )
