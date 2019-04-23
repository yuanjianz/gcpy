""" Core utilities for handling GEOS-Chem data """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import xarray as xr
import xbpch
import numpy as np
import json
import shutil

# JSON files to read
lumped_spc = 'lumped_species.json'
bpch_to_nc_names = 'bpch_to_nc_names.json'


def open_dataset(filename, **kwargs):
    """ Load and decode a dataset from an output file generated by GEOS-Chem

    This method inspects a GEOS-Chem output file and chooses a way to load it
    into memory as an xarray Dataset. Because two different libraries to
    support BPCH and netCDF outputs, you may need to pass additional keyword
    arguments to the function. See the Examples below.

    Parameters
    ----------
    filename : str
        Path to a GEOS-Chem output file (netCDF or BPCH format) which can be
        loaded through either xarray or xbpch. Note that xarray conventions for
        netCDF files apply.
    **kwargs
        Additional keyword arguments to be passed directly to
        `xarray.open_dataset` or `xbpch.open_bpchdataset`.

    Returns
    -------
    dataset : xarray.Dataset
        The dataset loaded from the referenced filename.

    See Also
    --------
    xarray.open_dataset
    xbpch.open_bpchdataset
    open_mfdataset

    Examples
    --------

    Open a legacy BPCH output file:

    >>> ds = open_dataset("my_GEOS-Chem_run.bpch",
    ...                   tracerinfo_file='tracerinfo.dat',
    ...                   diaginfo_file='diaginfo.dat')

    Open a netCDF output file, but disable metadata decoding:
    >>> ds = open_dataset("my_GCHP_data.nc",
    ...                   decode_times=False, decode_cf=False)

    """

    basename, file_extension = os.path.splitext(filename)

    if file_extension == '.bpch':
        _opener = xbpch.open_bpchdataset
    elif file_extension == '.nc':
        _opener = xr.open_dataset
    else:
        raise ValueError("Found unknown file extension ({}); please pass a "
                         "BPCH or netCDF file with extension 'bpch' or 'nc'."
                         .format(file_extension))

    return _opener(filename, **kwargs)


def open_mfdataset(filenames, concat_dim='time', compat='no_conflicts',
                   preprocess=None, lock=None, **kwargs):
    """ Load and decode multiple GEOS-Chem output files as a single Dataset.

    Parameters
    ----------
    filenames : list of strs
        Paths to GEOS-Chem output files to load. Must have the same extension
        and be able to be concatenated along some common axis.
    concat_dim : str, default='time'
        Dimension to concatenate Datasets over. We default to "time" since this
        is how GEOS-Chem splits output files.
    compat : {'identical', 'equals', 'broadcast_equals',
              'no_conflicts'}, optional
        String indicating how to compare variables of the same name for
        potential conflicts when merging:
        - 'broadcast_equals': all values must be equal when variables are
          broadcast against each other to ensure common dimensions.
        - 'equals': all values and dimensions must be the same.
        - 'identical': all values, dimensions and attributes must be the
          same.
        - 'no_conflicts': only values which are not null in both datasets
          must be equal. The returned dataset then contains the combination
          of all non-null values.
    preprocess : callable (optional)
        A pre-processing function to apply to each Dataset prior to
        concatenation
    lock : False, True, or threading.Lock (optional)
        Passed to :py:func:`dask.array.from_array`. By default, xarray
        employs a per-variable lock when reading data from NetCDF files,
        but this model has not yet been extended or implemented for bpch files
        and so this is not actually used. However, it is likely necessary
        before dask's multi-threaded backend can be used
    **kwargs
        Additional keyword arguments to be passed directly to
        `xbpch.open_mfbpchdataset` or `xarray.open_mfdataset`.

    Returns
    -------
    dataset : xarray.Dataset
        A dataset containing the data in the specified input filenames.

    See Also
    --------
    xarray.open_mfdataset
    xbpch.open_mfbpchdataset
    open_dataset

    """

    try:
        test_fn = filenames[0]
    except:
        raise ValueError("Must pass a list with at least one filename")

    basename, file_extension = os.path.splitext(test_fn)

    if file_extension == '.bpch':
        _opener = xbpch.open_mfbpchdataset
    elif file_extension == '.nc':
        _opener = xr.open_mfdataset
    else:
        raise ValueError("Found unknown file extension ({}); please pass a "
                         "BPCH or netCDF file with extension 'bpch' or 'nc'."
                         .format(file_extension))

    return _opener(filenames, concat_dim=concat_dim, compat=compat,
                   preprocess=preprocess, lock=lock, **kwargs)


def get_gcc_filepath(outputdir, collection, day, time):
    if collection == 'Emissions':
        filepath = os.path.join(outputdir, 'HEMCO_diagnostics.{}{}.nc'.format(day,time))
    else:
        filepath = os.path.join(outputdir, 'GEOSChem.{}.{}_{}z.nc4'.format(collection,day,time))
    return filepath


def get_gchp_filepath(outputdir, collection, day, time):
    filepath = os.path.join(outputdir, 'GCHP.{}.{}_{}z.nc4'.format(collection,day,time))
    return filepath


def check_paths(refpath, devpath):
    '''
    Checks to see if paths to data files exist.

    Args:
        refpath : str
            Path to the "Reference" data.

        devpath : str
            Path to the "Development" data.
    '''

    if not os.path.exists(refpath):
        print('ERROR! Path 1 does not exist: {}'.format(refpath))
    else:
        print('Path 1 exists: {}'.format(refpath))
    if not os.path.exists(devpath):
        print('ERROR! Path 2 does not exist: {}'.format(devpath))
    else:
        print('Path 2 exists: {}'.format(devpath))

        
def compare_varnames(refdata, devdata, quiet=False):
    '''
    Finds variables that are common to two xarray Dataset objects.

    Args:
        refdata : xarray Dataset
            The first Dataset to be compared.
            (This is often referred to as the "Reference" Dataset.)

        devdata : xarray Dataset
            The second Dataset to be compared.
            (This is often referred to as the "Development" Dataset.)

        quiet : boolean
            If True, will suppress printing to stdout.
            quiet is set to False by default.

    Returns:
        commonvars: list of strs
            Variables that are common to both refdata and devdata,
            regardless of dimension.

        commonvars1D: list of strs
            Variables that are common to refdata and devdata,
            and that are 1-dimensional.

        commonvars2D: list of strs
            Variables that are common to refdata and devdata,
            and that are 2-dimensional.

        commonvars3D: list of strs
            Variables that are common to refdata and devdata,
            and that are 3-dimensional.

    Examples:
        >>> import gcpy
        >>> import xarray as xr
        >>> refdata = xr.open_dataset("ref_data_file.nc")
        >>> devdata = xr.open_dataset("dev_data_file.nc")
        >>> [commonvars, commonvars1D, commonvars2D, commonvars3D ] = gcpy.compare_varnames(refdata, devdata)
    '''
    refvars = [k for k in refdata.data_vars.keys()]
    devvars= [k for k in devdata.data_vars.keys()]
    commonvars = sorted(list(set(refvars).intersection(set(devvars))))
    refonly = [v for v in refvars if v not in devvars]
    devonly = [v for v in devvars if v not in refvars]
    dimmismatch = [v for v in commonvars if refdata[v].ndim != devdata[v].ndim]
    commonvars1D = [v for v in commonvars if refdata[v].ndim == 2]
    commonvars2D = [v for v in commonvars if refdata[v].ndim == 3]
    commonvars3D = [v for v in commonvars if refdata[v].ndim == 4]
    
    # Print information on common and mismatching variables, as well as dimensions
    if quiet == False:
        print('{} common variables'.format(len(commonvars)))
        if len(refonly) > 0:
            print('{} variables in ref only (skip)'.format(len(refonly)))
            print('   Variable names: {}'.format(refonly))
        else:
            print('0 variables in ref only')
            if len(devonly) > 0:
                print('{} variables in dev only (skip)'.format(len(devonly)))
                print('   Variable names: {}'.format(devonly))
            else:
                print('0 variables in dev only')
                if len(dimmismatch) > 0:
                    print('{} common variables have different dimensions'.format(len(dimmismatch)))
                    print('   Variable names: {}'.format(dimmismatch))
                else:
                    print('All variables have same dimensions in ref and dev')

    return [commonvars, commonvars1D, commonvars2D, commonvars3D]


def compare_stats(refdata, refstr, devdata, devstr, varname):
    '''
    Prints out global statistics (array sizes, mean, min, max, sum)
    from two xarray Dataset objects.

    Args:
        refdata : xarray Dataset
            The first Dataset to be compared.
            (This is often referred to as the "Reference" Dataset.)

        refstr : str
            Label for refdata to be used in the printout

        devdata : xarray Dataset
            The second Dataset to be compared.
            (This is often referred to as the "Development" Dataset.)

        devstr : str
            Label for devdata to be used in the printout

        varname : str
            Variable name for which global statistics will be printed out.

    Returns:
        None

    Examples:
        >>> import gcpy
        >>> import xarray as xr
        >>> refdata = xr.open_dataset("ref_data_file.nc")
        >>> devdata = xr.open_dataset("dev_data_file.nc")
        >>> gcpy.compare_stats(ds_ref, "Ref", ds_dev, "Dev", "EmisNO2_Anthro")

        Data units:
            Ref:  molec/cm2/s
            Dev:  molec/cm2/s
        Array sizes:
            Ref:  (1, 47, 46, 72)
            Dev:  (1, 47, 46, 72)
        Global stats:
          Mean:
            Ref:  1770774.125
            Dev:  1770774.125
          Min:
            Ref:  0.0
            Dev:  0.0
          Max:
            Ref:  11548288000.0
            Dev:  11548288000.0
          Sum:
            Ref:  275645792256.0
            Dev:  275645792256.0
    '''

    refvar = refdata[varname]
    devvar = devdata[varname]
    units = refdata[varname].units
    print('Data units:')
    print('    {}:  {}'.format(refstr,units))
    print('    {}:  {}'.format(devstr,units))
    print('Array sizes:')
    print('    {}:  {}'.format(refstr,refvar.shape))
    print('    {}:  {}'.format(devstr,devvar.shape))
    print('Global stats:')
    print('  Mean:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.mean(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.mean(),20)))
    print('  Min:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.min(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.min(),20)))
    print('  Max:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.max(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.max(),20)))
    print('  Sum:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.sum(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.sum(),20)))

    
def get_collection_data(datadir, collection, day, time):
    datafile = get_gcc_filepath(datadir, collection, day, time)
    if not os.path.exists(datafile):
        print('ERROR! File does not exist: {}'.format(datafile))
    data_ds = xr.open_dataset(datafile)
    return data_ds


def get_gchp_collection_data(datadir, collection, day, time):
    datafile = get_gchp_filepath(datadir, collection, day, time)
    data_ds = xr.open_dataset(datafile)
    return data_ds


def convert_bpch_names_to_netcdf_names(ds, inplace=False, verbose=False):

    '''
    Function to convert the non-standard bpch diagnostic names
    to names used in the GEOS-Chem netCDF diagnostic outputs.
    
    Arguments:
    ds      : The xarray Dataset object whose names are to be replaced.
    
    inplace : If inplace=True, then the variable names in ds will be 
              renamed in-place.  Otherwise a copy of ds will be created.
              NOTE: inPlace=False is now the default setting, because
              this invokes an xarray method that will become deprecated.

    verbose : Turns on verbose print output

    NOTE: Only the diagnostic names needed for the 1-month benchmark
    plots have been added at this time.  To make this a truly general
    tool, we can consider adding the diagnostic names for the GEOS-Chem
    specialtiy simulations later on.
    '''

    # Names dictionary (key = bpch id, value[0] = netcdf id,
    # value[1] = action to create full name using id)
    # Now read from JSON file (bmy, 4/5/19)
    jsonfile = os.path.join(os.path.dirname(__file__), bpch_to_nc_names)
    names = json.load(open(jsonfile))

    # define some special variable to overwrite above
    special_vars = {'AerMassPM25'  : 'PM25',
                    'AerMassbiogOA': 'TotalBiogenicOA',
                    'AerMasssumOA' : 'TotalOA',
                    'AerMasssumOC' : 'TotalOC',
                    'AerMassBNO'   : 'BetaNO',
                    'AerMassOC'    : 'OC',
                    'Met_AIRNUMDE' : 'Met_AIRNUMDEN',
                    'Met_UWND'     : 'Met_U',
                    'Met_VWND'     : 'Met_V',
                    'Met_CLDTOP'   : 'Met_CLDTOPS',
                    'Met_GWET'     : 'Met_GWETTOP',
                    'Met_PRECON'   : 'Met_PRECCON',
                    'Met_PREACC'   : 'Met_PRECTOT',
                    'Met_PBL'      : 'Met_PBLH' }

    # Python dictionary for variable name replacement
    old_to_new = {}

    # Loop over all variable names in the data set
    for variable_name in ds.data_vars:

        # Check if name matches anything in dictionary. Give warning if not.
        oldid = ''
        newid = ''
        idaction = ''
        for key in names:
            if key in variable_name:
                if names[key][1] == 'skip':
                    # Verbose output
                    if verbose:
                        print("WARNING: skipping {}".format(key))
                else:
                    oldid = key
                    newid = names[key][0]
                    idaction = names[key][1]
                break

        # Go to the next line if no definition was found
        if oldid == '' or newid == '' or idaction == '':
            continue

        # If fullname replacement:
        if idaction == 'replace':
            oldvar = oldid
            newvar = newid

            # Update the dictionary of names with this pair
            old_to_new.update({variable_name : newvar})

        # For all the rest:
        else:
            linearr = variable_name.split("_")
            varstr = linearr[-1]
            oldvar = oldid + varstr

            # Most append cases just append with underscore
            if oldid in ['IJ_AVG_S_', 'RN_DECAY_', 'WETDCV_S_', 'WETDLS_S_',
                         'BXHGHT_S_', 'DAO_FLDS_', 'DAO_3D_S_', 'PL_SUL_',
                         'CV_FLX_S_', 'EW_FLX_S_', 'NS_FLX_S_', 'UP_FLX_S_',
                         'MC_FRC_S_', 'JV_MAP_S_' ]:
     
                # Skip certain fields that will cause conflicts w/ netCDF
                if oldid in [ 'DAO_FLDS_PS_PBL', 'DAO_FLDS_TROPPRAW' ]:

                    # Verbose output
                    if verbose:
                        print( 'Skipping: {}'.format(oldid) )
                else:
                    newvar = newid + '_' +varstr

            # Special handling for J-values: The bpch variable names all
            # begin with "J" (e.g. JNO, JACET), so we need to strip the first
            # character of the variable name manually (bmy, 4/8/19)
            if oldid == 'JV_MAP_S_':
                newvar = newid + '_' + varstr[1:]

            # IJ_SOA_S_
            elif oldid == 'IJ_SOA_S_':
               newvar = newid + varstr

            # DRYD_FLX_, DRYD_VEL_
            elif 'DRYD_' in oldid:
                newvar = newid + '_' + varstr[:-2]

            # BIOBSRCE_, BIOFSRCE_, BIOGSRCE_. ANTHSRCE_
            elif oldid in ['BIOBSRCE_', 'BIOFSRCE_', 'BIOGSRCE_', 
                           'ANTHSRCE_' ]:
                newvar = 'Emis' + varstr +'_' + newid
            
            # If nothing found...
            else:
                
                # Verbose output
                if verbose:
                    print("WARNING: Nothing defined for: {}".
                          format(variable_name))
                continue

          # Overwrite certain variable names
            if newvar in special_vars:
                newvar = special_vars[newvar]

            # Update the dictionary of names with this pair
            old_to_new.update({variable_name : newvar})

    # Verbose output
    if verbose:
        print("\nList of bpch names and netCDF names")
        for key in old_to_new:
            print("{} ==> {}".format(key.ljust(25),old_to_new[key].ljust(40)))

    # Rename the variables in the dataset
    if verbose:
        print( "\nRenaming variables in the data...")
    ds = ds.rename(name_dict=old_to_new, inplace=inplace)
    
    # Return the dataset
    return ds


def get_lumped_species_definitions():
    jsonfile = os.path.join(os.path.dirname(__file__), lumped_spc)
    with open(jsonfile, 'r') as f:
        lumped_spc_dict = json.loads(f.read())
    return lumped_spc_dict


def archive_lumped_species_definitions(dst):
    src = os.path.join(os.path.dirname(__file__), lumped_spc)
    print('Archiving {} in {}'.format(lumped_spc, dst))
    shutil.copyfile(src, os.path.join(dst, lumped_spc))

    
def add_lumped_species_to_dataset(ds, lspc_dict={}, lspc_json='',
                                  verbose=False, overwrite=False, prefix='SpeciesConc_'):

    # Default is to add all benchmark lumped species. Can overwrite by passing a dictionary
    # or a json file path containing one
    assert not (lspc_dict != {} and lspc_json != ''), 'Cannot pass both lspc_dict and lspc_json. Choose one only.'
    if lspc_dict == {} and lspc_json == '':
        lspc_dict = get_lumped_species_definitions()
    elif lspc_dict == {} and lspc_json != '':
        with open(lspc_json, 'r') as f:
            lspc_dict = json.loads(f.read())

    for lspc in lspc_dict:
        varname_new = prefix+lspc
        if varname_new in ds.data_vars and overwrite:
            ds.drop(varname_new)
        else:
            assert varname_new not in ds.data_vars, '{} already in dataset. To overwrite pass overwrite=True.'.format(varname_new)
        if verbose:
            print('Creating {}'.format(varname_new))
        for i, spc in enumerate(lspc_dict[lspc]):
            varname = prefix+spc
            if varname not in ds.data_vars:
                print('Warning: {} needed for {} not in dataset.'.format(spc,lspc))
                continue
            if verbose:
                print(' -> adding {} with scale {}'.format(spc,lspc_dict[lspc][spc]))
            if i == 0:
                darr = ds[varname] * lspc_dict[lspc][spc]
                units = ds[varname].units
            else:
                darr = darr + ds[varname] * lspc_dict[lspc][spc]
        darr.name = varname_new
        darr.attrs['units'] = units
        ds = xr.merge([ds,darr])
    return ds


def filter_names(names, text=''):
    '''
    Returns elements in a list that match a given substring.
    Can be used in conjnction with compare_varnames to return a subset
    of variable names pertaining to a given diagnostic type or species.
    
    Args:
        names: list of strs

        text: str
            Target text string for restricting the search.
    
    Returns:
        filtered_names: list of strs
            Returns all elements of names that contains the substring
            specified by the "text" argument.  If "text" is omitted,
            then the original contents of names will be returned.
        
    Examples:
        Obtain a list of variable names that contain the substrings
        "CO", "NO", and "O3":
        
        >>> import gcpy
        >>> import xarray as xr
        >>> refdata = xr.open_dataset("ref_data_file.nc")
        >>> devdata = xr.open_dataset("dev_data_file.nc")
        >>> [var, var1D, var2D, var3D] = gcpy.compare_varnames(refdata, devdata)
        >>> var_CO = gcpy.filter_names(var, "CO")
        >>> var_NO = gcpy.filter_names(var, "NO")
        >>> var_O3 = gcpy.filter_names(var, "O3")
    '''

    if text != '':
        filtered_names = [k for k in names if text in k]
    else:
        filtered_names = [k for k in names if k]

    return filtered_names
    

def divide_dataset_by_dataarray(ds, dr, varlist=None):
    '''
    Divides variables in an xarray Dataset object by a single DataArray
    object.  Will also make sure that the Dataset variable attributes
    are preserved.

    This method can be useful for certain types of model diagnostics
    that have to be divided by a counter array.  For example, local
    noontime J-value variables in a Dataset can be divided by the
    fraction of time it was local noon in each grid box, etc.

    Args:
        ds: xarray Dataset
            The Dataset object containing variables to be divided.

        dr: xarray DataArray
            The DataArray object that will be used to divide the
            variables of ds.

    Kewyword Args (optional):
        varlist: list
            If passed, then only those variables of ds that are listed
            in varlist will be divided by dr.  Otherwise, all variables
            of ds will be divided by dr.

    Returns:
        ds_new : xarray Dataset
            A new xarray Dataset object with its variables divided by dr.
    '''

    # -----------------------------
    # Check arguments
    # -----------------------------
    if not isinstance(ds, xr.Dataset):
        raise TypeError('The ds argument must be of type xarray.Dataset!')

    if not isinstance(dr, xr.DataArray):
        raise TypeError('The dr argument must be of type xarray.DataArray!')

    if varlist == None:
        varlist = ds.data_vars.keys()

    # -----------------------------
    # Do the division
    # -----------------------------
    for v in varlist:

        # Save attributes from each element of the Dataset object
        attrs = ds[v].attrs

        # Divide each variable of ds by dr
        ds[v] = ds[v] / dr

        # Save the original attributes back to the DataArray
        ds[v].attrs = attrs

    # -----------------------------
    # Return the modified Dataset
    # -----------------------------
    return ds
