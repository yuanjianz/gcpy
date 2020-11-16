Plotting
========

This page describes in depth the plotting capabilities of GCPy, including possible argument values for every plotting function.



compare_single_level and compare_zonal_mean
-------------------------------------------

``gcpy.plot.compare_single_level()`` and ``gcpy.plot.compare_zonal_mean()`` both generate six panel plots
comparing variables between two datasets. They share significant structural overlap both in
output appearance and code implementation. This section gives an overview of the components
of the plots generated by these functions, their shared arguments, and features unique to each function.


Shared structure
~~~~~~~~~~~~~~~~

Both ``compare_single_level()`` and ``compare_zonal_mean()`` generate a six panel plot for each variable passed.
These plots can either be saved to PDFs or generated sequentially for visualization in the Matplotlib GUI using ``matplotlib.pyplot.show()``.
Each plot uses data passed from a reference (``Ref``) dataset and a development (``Dev``) dataset.

Each panel has a title describing the type of panel, a colorbar for the values plotted in that panel, and the units of the data plotted in that panel.
The upper two panels of each plot show actual values from the Ref (left) and Dev (right) datasets for a given variable.
The middle two panels show the difference (``Dev - Ref``) between the values in the Dev dataset and the values in the Ref dataset.
The left middle panel uses a full dynamic color map, while the right middle panel caps the color map at the 5th and 95th percentiles.
The bottom two panels show the ratio (``Dev/Ref``) between the values in the Dev dataset and the values in the Ref Dataset.
The left bottom panel uses a full dynamic color map, while the right bottom panel caps the color map at 0.5 and 2.0.

Both ``compare_single_level()`` and ``compare_zonal_mean()`` have four positional (required) arguments.

Arguments:
^^^^^^^^^^

.. option:: refdata : xarray.Dataset

   Dataset used as reference in comparison

.. option:: refstr : str OR list of str

   String description for reference data to be used in plots OR list containing [ref1str, ref2str] for diff-of-diffs plots

.. option:: devdata : xarray.Dataset

   Dataset used as development in comparison

.. option:: devstr : str OR list of str

   String description for development data to be used in plots
   OR list containing [dev1str, dev2str] for diff-of-diffs plots


``refstr`` and ``devstr`` title the top two panels of each six panel plot.

A basic script that calls ``compare_zonal_mean()`` or ``compare_single_level()`` looks like:

.. code-block:: python

   import xarray as xr
   import gcpy.plot as gcplot
   import matplotlib.pyplot as plt
   
   file1 = '/path/to/ref'
   file2 = '/path/to/dev'
   ds1 = xr.open_dataset(file1)
   ds2 = xr.open_dataset(file2)
   gcplot.compare_zonal_mean(ds1, 'Ref run', ds2, 'Dev run')
   #gcplot.compare_single_level(ds1, 'Ref run', ds2, 'Dev run')
   plt.show()


``compare_single_level()`` and ``compare_zonal_mean()`` also share many keyword arguments.
Some of these arguments are plotting options that change the format of the plots, e.g. choosing to convert units to ug/m\ :sup:`3`,
which are automatically handled if you do not specify a value for that argument.

Other arguments are necessary to achieve a correct plot depending on the format of ``refdata`` and ``devdata`` and require you
to know certain traits of your input data. For example, you must specify if one of the datasets should be flipped vertically
if Z coordinates in that dataset do not denote decreasing pressure as Z index increases, otherwise the vertical coordinates between
your two datasets may be misaligned and result in an undesired plotting outcome.

The ``n_job`` argument governs the parallel plotting settings of ``compare_single_level()`` and ``compare_zonal_mean()`` . 
GCPy uses the joblib library to create plots in parallel. Due to limitations with matplotlib, this parallelization creates plots (pages)
in parallel rather than individual panels on a single page. Parallel plot creation is not enabled when you do not save to a PDF. 
The default value of ``n_job=-1`` allows the function call to automatically scale up to, at most, the number of cores available on your system.
On systems with higher (12+) core counts, the max number of cores is not typically reached because of the process handling mechanics of joblib.
However, on lower-end systems with lower core counts or less available memory, it is advantageous to use ``n_job`` to limit the max number of processes.

Shared keyword arguments:
^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: varlist : list of str

      List of xarray dataset variable names to make plots for

      Default value: None (will compare all common variables)

.. option:: itime : int

      Dataset time dimension index using 0-based system. Can only plot values from one time index 
      in a single function call.

      Default value: 0

.. option:: refmet : xarray.Dataset

      Dataset containing ref meteorology. Needed for area-based normalizations / ug/m3 unit conversions.

      Default value: None

.. option:: devmet : xarray.Dataset

      Dataset containing dev meteorology. Needed for area-based normalizations / ug/m3 unit conversions.  

      Default value: None

.. option:: weightsdir : str

      Directory path for storing regridding weight files generated by xESMF.

      Default value: None (will create/store weights in current directory)

.. option:: pdfname : str

      File path to save plots as PDF.

      Default value: Empty string (will not create PDF)

.. option:: cmpres : str

      String description of grid resolution at which to compare datasets. 
      The possible formats are 'int' (e.g. '48' for c48) for a cubed-sphere resolution 
      or 'latxlon' (e.g. '4x5') for a lat/lon resolution.

      Default value: None (will compare at highest resolution of Ref and Dev)

.. option:: match_cbar : bool

      Set this flag to True to use same the colorbar bounds for both Ref and Dev plots.
      This only applies to the top two panels of each plot.

      Default value: True

.. option:: normalize_by_area : bool

      Set this flag to True to to normalize raw data in both Ref and Dev datasets by grid area.
      Either input ref and dev datasets must include AREA variable in m2 if normalizing by area, 
      or refmet and devmet datasets must include Met_AREAM2 variable.

      Default value: False

.. option:: enforce_units : bool

      Set this flag to True force an error if the variables in the Ref and Dev datasets 
      have different units.

      Default value: True

.. option:: convert_to_ugm3 : bool

      Whether to convert data units to ug/m3 for plotting. refmet and devmet cannot be None
      if converting to ug/m3.

      Default value: False

.. option:: flip_ref : bool

      Set this flag to True to flip the vertical dimension of 3D variables in the Ref dataset.

      Default value: False

.. option:: flip_dev : bool

      Set this flag to True to flip the vertical dimension of 3D variables in the Dev dataset.

      Default value: False

.. option:: use_cmap_RdBu : bool

      Set this flag to True to use a blue-white-red colormap for plotting raw ref and dev data
      (the top two panels).

      Default value: False

.. option:: verbose : bool

      Set this flag to True to enable informative printout.

      Default value: False

.. option:: log_color_scale : bool

      Set this flag to True to enable plotting data (only the top two panels, not diffs) on a log color scale.

      Default value: False      

.. option:: extra_title_txt : str

      Specifies extra text (e.g. a date string such as "Jan2016")
      for the top-of-plot title.

      Default value: None      

.. option:: n_job : int

      Defines the number of simultaneous workers for parallel plotting. Only applicable when saving to PDF.
      Set to 1 to disable parallel plotting. Value of -1 allows the application to decide.

      Default value: -1

.. option:: sigdiff_list : list of str

      Returns a list of all quantities having significant
      differences (where |max(fractional difference)| > 0.1).

      Default value: []

.. option:: second_ref : xarray.Dataset

      A dataset of the same model type / grid as refdata, to be used in diff-of-diffs plotting.

      Default value: None

.. option:: second_dev : xarray.Dataset

      A dataset of the same model type / grid as devdata, to be used in diff-of-diffs plotting.

      Default value: None

.. option:: spcdb_dir : str

      Directory containing species_database.yml file. This file is used for unit conversions to ug/m3.
      GEOS-Chem run directories include a copy of this file which may be more up-to-date than the version
      included with GCPy.

      Default value: Path of GCPy code repository

.. option:: sg_ref_path : str

      Path to NetCDF file containing stretched-grid info (in attributes) for the ref dataset.

      Default value: '' (will not be read in)

.. option:: sg_dev_path : str

      Path to NetCDF file containing stretched-grid info (in attributes) for the dev dataset.

      Default value: '' (will not be read in)

   
      
compare_single_level
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def compare_single_level(refdata, refstr, devdata, devstr,
             varlist=None, ilev=0, itime=0,
             refmet=None, devmet=None, weightsdir='.',
              pdfname="", cmpres=None, match_cbar=True,
             normalize_by_area=False, enforce_units=True,
             convert_to_ugm3=False, flip_ref=False, flip_dev=False,
             use_cmap_RdBu=False, verbose=False, log_color_scale=False,
             extra_title_txt=None, extent = [-1000, -1000, -1000, -1000],
             n_job=-1, sigdiff_list=[], second_ref=None, second_dev=None,
             spcdb_dir=os.path.dirname(__file__), sg_ref_path='', sg_dev_path='',
             ll_plot_func='imshow', **extra_plot_args
             ):

                      
``compare_single_level()`` features several keyword arguments that are not relevant to ``compare_zonal_mean()``,
including specifying which level to plot, the lat/lon extent of the plots, and which underlying ``matplotlib.plot`` 
function to use for plotting.

Function-specific keyword arguments:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: ilev : int 

      Dataset level dimension index using 0-based system

      Default value: 0

.. option:: extent : list of float

      Defines the extent of the region to be plotted in form 
      [minlon, maxlon, minlat, maxlat]. Default value plots extent of input grids.

      Default value: [-1000, -1000, -1000, -1000]

.. option:: ll_plot_func : str

      Function to use for lat/lon single level plotting with possible values 'imshow' and 'pcolormesh'.
      imshow is much faster but is slightly displaced when plotting from dateline to dateline and/or pole to pole.

      Default value: 'imshow'

.. option:: **extra_plot_args

      Any extra keyword arguments are passed through the plotting functions to be used 
      in calls to pcolormesh() (CS) or imshow() (Lat/Lon).


compare_zonal_mean
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def compare_zonal_mean(refdata, refstr, devdata, devstr,
            varlist=None, itime=0, refmet=None, devmet=None,
            weightsdir='.', pdfname="", cmpres=None,
            match_cbar=True, pres_range=[0, 2000],
            normalize_by_area=False, enforce_units=True,
            convert_to_ugm3=False, flip_ref=False, flip_dev=False,
            use_cmap_RdBu=False, verbose=False, log_color_scale=False,
            log_yaxis=False, extra_title_txt=None, n_job=-1, sigdiff_list=[],
            second_ref=None, second_dev=None, spcdb_dir=os.path.dirname(__file__),
            sg_ref_path='', sg_dev_path='', ref_vert_params=[[],[]], 
            dev_vert_params=[[],[]], **extra_plot_args
            ):


``compare_zonal_mean()`` features several keyword arguments that are not relevant to ``compare_single_level()``,
including specifying the pressure range to plot (defaulting to the complete atmosphere), whether the y-axis of the plots
(pressure) should be in log format, and hybrid vertical grid parameters to pass if one or more of Ref and Dev do not use
the typical 72-level or 47-level grids.

Function-specific keyword arguments:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: pres_range : list of ints

      Pressure range of levels to plot [hPa]. The vertical axis will
      span the outer pressure edges of levels that contain pres_range
       endpoints.
      Default value: [0,2000]

.. option:: log_yaxis : bool

      Set this flag to True if you wish to create zonal mean
      plots with a log-pressure Y-axis.

      Default value: False

.. option:: ref_vert_params : list of list-like types

      Hybrid grid parameter A in hPa and B (unitless). Needed if ref grid is not 47 or 72 levels.

      Default value: [[], []]

.. option:: dev_vert_params : list of list-like types

      Hybrid grid parameter A in hPa and B (unitless). Needed if dev grid is not 47 or 72 levels.

      Default value: [[], []]

.. option:: **extra_plot_args

      Any extra keyword arguments are passed through the plotting functions to be used 
      in calls to pcolormesh().      



Single_panel
------------

.. code-block:: python

   def single_panel(plot_vals, ax=None, plot_type="single_level",
       grid={}, gridtype="", title="fill",comap=WhGrYlRd,
       norm=[],unit="",extent=(None, None, None, None),
       masked_data=None,use_cmap_RdBu=False,
       log_color_scale=False, add_cb=True,
       pres_range=[0, 2000], pedge=np.full((1, 1), -1),
       pedge_ind=np.full((1,1), -1), log_yaxis=False,
       xtick_positions=[], xticklabels=[], proj=ccrs.PlateCarree(),
       sg_path='', ll_plot_func="imshow", vert_params=[[],[]],
       pdfname="", **extra_plot_args
       ):


``gcpy.plot.single_panel()`` is used to create plots containing only one panel of GEOS-Chem data. 
This function is used within ``compare_single_level()`` and ``compare_zonal_mean()`` to generate each panel plot.
It can also be called directly on its own to quickly plot GEOS-Chem data in zonal mean or single level format.

.. code-block:: python

   import xarray as xr
   import gcpy.plot as gcplot
   import matplotlib.pyplot as plt
   
   ds = xr.open_dataset('GEOSChem.SpeciesConc.20160701_0000z.nc4')
   #get surface ozone
   plot_data = ds['SpeciesConc_O3'].isel(lev=0)
   
   gcplot.single_panel(plot_data)
   plt.show()

Currently ``single_panel()`` expects data with a 1-length ( or non-existent) time dimension,
as well as a 1-length or non-existent Z dimension for single level plotting, so you'll need to do some pre-processing of your input data as shown in the above code snippet.
``single_panel()`` contains a few amenities to help with plotting GEOS-Chem data, including automatic grid detection
for lat/lon or standard cubed-sphere xarray ``DataArray`` s. You can also pass NumPy arrays to plot, though you'll need to manually pass grid info in this case.


Arguments:
~~~~~~~~~~

In addition to the specific arguments listed below, any other keyword arguments will be forwarded to ``matplotlib.pyplot.imshow()`` / ``matplotlib.pyplot.pcolormesh()``.

.. option:: plot_vals : xarray.DataArray or numpy array

         Single data variable GEOS-Chem output to plot
   
.. option:: ax : matplotlib axes         

         Axes object to plot information

         Default value: None (Will create a new axes)

.. option:: plot_type : str

         Either "single_level" or "zonal_mean"

         Default value: "single_level"

.. option:: grid : dict

         Dictionary mapping plot_vals to plottable coordinates

         Default value: {} (will attempt to read grid from plot_vals)

.. option:: gridtype : str

         "ll" for lat/lon or "cs" for cubed-sphere

         Default value: "" (will automatically determine from grid)

.. option:: title : str

         Title to put at top of plot

         Default value: "fill" (will use name attribute of plot_vals if available)

.. option:: comap : matplotlib Colormap

         Colormap for plotting data values

         Default value: WhGrYlRd

.. option:: norm : list

         List with range [0..1] normalizing color range for matplotlib methods

         Default value: [] (will determine from plot_vals)

.. option:: unit : str

         Units of plotted data

         Default value: "" (will use units attribute of plot_vals if available)

.. option:: extent : tuple (minlon, maxlon, minlat, maxlat)

         Describes minimum and maximum latitude and longitude of input data

         Default value: (None, None, None, None) (Will use full extent of plot_vals
         if plot is single level.

.. option:: masked_data : numpy array

         Masked area for avoiding near-dateline cubed-sphere plotting issues

         Default value: None (will attempt to determine from plot_vals)

.. option:: use_cmap_RdBu : bool

         Set this flag to True to use a blue-white-red colormap

         Default value: False

.. option:: log_color_scale : bool

         Set this flag to True to use a log-scale colormap

         Default value: False

.. option:: add_cb : bool

         Set this flag to True to add a colorbar to the plot

         Default value: True

.. option:: pres_range : list of int

         Range from minimum to maximum pressure for zonal mean plotting

         Default value: [0, 2000] (will plot entire atmosphere)

.. option:: pedge : numpy array

         Edge pressures of vertical grid cells in plot_vals for zonal mean plotting

         Default value: np.full((1, 1), -1) (will determine automatically)

.. option:: pedge_ind : numpy array

         Index of edge pressure values within pressure range in plot_vals for zonal mean plotting

         Default value: np.full((1, 1), -1) (will determine automatically)

.. option:: log_yaxis : bool

         Set this flag to True to enable log scaling of pressure in zonal mean plots

         Default value: False

.. option:: xtick_positions : list of float

         Locations of lat/lon or lon ticks on plot

         Default value: [] (will place automatically for zonal mean plots)

.. option:: xticklabels : list of str

         Labels for lat/lon ticks

         Default value: [] (will determine automatically from xtick_positions)

.. option:: sg_path : str

         Path to NetCDF file containing stretched-grid info (in attributes) for plot_vals

         Default value: '' (will not be read in)

.. option:: ll_plot_func : str

         Function to use for lat/lon single level plotting with possible values 'imshow' and 'pcolormesh'.
         imshow is much faster but is slightly displaced when plotting from dateline to dateline and/or pole to pole.

         Default value: 'imshow'

.. option:: vert_params : list(AP, BP) of list-like types

         Hybrid grid parameter A in hPa and B (unitless). Needed if grid is not 47 or 72 levels.

         Default value: [[], []]

.. option:: pdfname : str

         File path to save plots as PDF

         Default value: "" (will not create PDF)

.. option:: extra_plot_args : various

         Any extra keyword arguments are passed to calls to pcolormesh() (CS) or imshow() (Lat/Lon).
         

``single_panel()`` returns the following object:

.. option:: plot : matplotlib plot

         Plot object created from input


Benchmark Plotting Functions
----------------------------

``gcpy.benchmark`` contains several functions for plotting GEOS-Chem output in formats requested by the GEOS-Chem Steering Comittee.
The primary use of these functions is to create plots of most GEOS-Chem output variables divided into specific categories, 
e.g. species categories such as Aerosols or Bromine for the SpeciesConc diagnostic. In each category, these functions create 
single level PDFs for the surface and 500hPa and zonal mean PDFs for the entire atmosphere and only the stratosphere (defined a 1-100hPa).
For ``make_benchmark_emis_plots()``, only single level plots at the surface are produced.
All of these plotting functions include bookmarks within the generated PDFs that point to the pages containing each plotted quantity.
Thus these functions serve as tools for quickly creating comprehensive plots comparing two GEOS-Chem runs. These functions are used to create 
the publicly available plots for 1-month and 1-year benchmarks of new versions of GEOS-Chem. 

Many of these functions use pre-defined (via YAML files included in GCPy) lists of variables. If one dataset includes a variable but the other dataset does not, 
the data for that variable in the latter dataset will be considered to be NaN and will be plotted as such. 

Shared structure
~~~~~~~~~~~~~~~~

Each of the ``gcpy.benchmark.make_benchmark_*_plots()`` functions requires 4 arguments to specify the ref and dev datasets.

Arguments:
^^^^^^^^^^ 

.. option:: ref: str

         Path name for the "Ref" (aka "Reference") data set.

.. option:: refstr : str

         A string to describe ref (e.g. version number)

.. option:: dev : str

         Path name for the "Dev" (aka "Development") data set.
      This data set will be compared against the "Reference" data set.

.. option:: devstr : str

         A string to describe dev (e.g. version number)

Note that the ``ref`` and ``dev`` arguments in ``make_benchmark_*_plots()`` are the
paths to NetCDF files, rather than xarray Datasets as in ``compare_single_level()`` and ``compare_zonal_mean()``. The ``make_benchmark_*_plots()`` functions internally
open these files as xarray Datasets and pass those datasets to ``compare_single_level()`` and ``compare_zonal_mean()``. 

The benchmark plotting functions share several keyword arguments. Keyword arguments that do not share the same purpose across benchmark plotting
functions have ``NOTE:`` in the description.

Shared keyword arguments:
^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: dst : str

         A string denoting the destination folder where a
         PDF file containing plots will be written.

         Default value: ./benchmark.

.. option:: subdst : str

         A string denoting the sub-directory of dst where PDF
         files containing plots will be written.  In practice,
         subdst is only needed for the 1-year benchmark output,
         and denotes a date string (such as "Jan2016") that
         corresponds to the month that is being plotted.
         NOTE: Not available in wetdep_plots

         Default value: None   

.. option:: overwrite : bool

         Set this flag to True to overwrite previously created files in the
         destination folder (specified by the dst argument).

         Default value: False.

.. option:: verbose : bool

         Set this flag to True to print extra informational output.

         Default value: False.

.. option:: log_color_scale: bool

         Set this flag to True to enable plotting data (the top two panels
         of each plot, not diffs) on a log color scale.

         Default value: False

.. option:: sigdiff_files : list of str

         Filenames that will contain the list of quantities having
         significant differences between datasets. Three files are used:
         one for surface, one for 500hPa, and one for zonal mean.
         These lists are needed in order to fill out the benchmark
         approval forms.
         NOTE: Not available in wetdep_plots

         Default value: None

.. option:: spcdb_dir : str

         Directory containing species_database.yml file. This file is used for unit conversions to ug/m3.
         GEOS-Chem run directories include a copy of this file which may be more up-to-date than the version
         included with GCPy.

         Default value: Path of GCPy code repository

.. option:: weightsdir : str
         Directory in which to place (and possibly reuse) xESMF regridder netCDF files.

         Default value: '.'

.. option:: n_job : int

         Defines the number of simultaneous workers for parallel plotting.
         Set to 1 to disable parallel plotting. Value of -1 allows the application to decide.
         NOTE: In make_benchmark_conc_plots(), parallelization occurs at the species category level.
         In all other functions, parallelization occurs within calls to compare_single_level()
         and compare_zonal_mean().

         Default value: -1 in make_benchmark_conc_plots, 1 in all others

   
make_benchmark_aod_plots
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def make_benchmark_aod_plots(ref, refstr, dev, devstr, varlist=None,
      dst="./benchmark", subdst=None, overwrite=False, verbose=False,
      log_color_scale=False, sigdiff_files=None, weightsdir='.', n_job=-1,
      spcdb_dir=os.path.dirname(__file__)
   ):

      """
      Creates PDF files containing plots of column aerosol optical
      depths (AODs) for model benchmarking purposes.
   """


Function-specific keyword args:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: varlist : list of str

   List of AOD variables to plot.  If not passed, then all
   AOD variables common to both Dev and Ref will be plotted.
   Use the varlist argument to restrict the number of
   variables plotted to the pdf file when debugging.

   Default value: None
   
   
This function creates column optical depth plots using the Aerosols diagnostic output. 


make_benchmark_conc_plots
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def make_benchmark_conc_plots(ref, refstr, dev, devstr, dst="./benchmark",
      subdst=None, overwrite=False, verbose=False, collection="SpeciesConc",
      benchmark_type="FullChemBenchmark", plot_by_spc_cat=True, restrict_cats=[],
      plots=["sfc", "500hpa", "zonalmean"], use_cmap_RdBu=False, log_color_scale=False,
      sigdiff_files=None, normalize_by_area=False, cats_in_ugm3=["Aerosols", "Secondary_Organic_Aerosols"],
      areas=None, refmet=None, devmet=None, weightsdir='.', n_job=-1, second_ref=None
      second_dev=None, spcdb_dir=os.path.dirname(__file__)
   ):
      """
      Creates PDF files containing plots of species concentration
      for model benchmarking purposes.
   """


Function-specific keyword args:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. option:: collection : str

   Name of collection to use for plotting.

   Default value: "SpeciesConc"

.. option:: benchmark_type: str

   A string denoting the type of benchmark output to plot,
   either FullChemBenchmark or TransportTracersBenchmark. 

   Default value: "FullChemBenchmark"      

.. option:: plot_by_spc_cat: logical

   Set this flag to False to send plots to one file rather
   than separate file per category.

   Default value: True

.. option:: restrict_cats : list of str

   List of benchmark categories in benchmark_categories.yml to make
   plots for. If empty, plots are made for all categories.

   Default value: empty

.. option:: plots : list of str

   List of plot types to create.

   Default value: ['sfc', '500hpa', 'zonalmean']

.. option:: normalize_by_area: bool

   Set this flag to true to enable normalization of data
   by surfacea area (i.e. kg s-1 --> kg s-1 m-2).

   Default value: False

.. option:: cats_in_ugm3: list of str

   List of benchmark categories to to convert to ug/m3

   Default value: ["Aerosols", "Secondary_Organic_Aerosols"]

.. option:: areas : dict of xarray DataArray:

   Grid box surface areas in m2 on Ref and Dev grids.

   Default value: None

.. option:: refmet : str

   Path name for ref meteorology

   Default value: None

.. option:: devmet : str

   Path name for dev meteorology  

     Default value: None

.. option:: second_ref: str

   Path name for a second "Ref" (aka "Reference") data set for
   diff-of-diffs plotting. This dataset should have the same model
   type and grid as ref.

   Default value: None

.. option:: second_dev: str

   Path name for a second "Ref" (aka "Reference") data set for
   diff-of-diffs plotting. This dataset should have the same model
   type and grid as ref.

   Default value: None


This function creates species concentration plots using the ``SpeciesConc`` diagnostic output by default. This function is the only 
benchmark plotting function that supports diff-of-diffs plotting, in which 4 datasets are passed and the differences between two groups
of Ref datasets vs. two groups of Dev datasets is plotted (typically used for comparing changes in GCHP vs. changes in GEOS-Chem Classic across
model versions). This is also the only benchmark plotting function that sends plots to separate folders based on category 
(as denoted by the ``plot_by_spc_cat`` flag). The full list of species categories is denoted in ``benchmark_categories.yml`` (included in GCPy) as follows:  

.. code-block:: python
   
   """
   FullChemBenchmark:
      Aerosols:
         Dust: DST1, DST2, DST3, DST4
         Inorganic: NH4, NIT, SO4
         OC_BC: BCPI, BCPO, OCPI, OCPO
         SOA: Complex_SOA, Simple_SOA
         Sea_Salt: AERI, BrSALA, BrSALC, ISALA, ISALC, NITs, 
            SALA, SALAAL, SALACL, SALC, SALCAL, SALCCL, SO4s
      Bromine: Bry, BrOx, Br, Br2, BrCl, BrNO2, BrNO3, BrO,
         CH3Br, CH2Br2, CHBr3, HOBr, HBr
      Chlorine: Cly, ClOx, Cl, ClO, Cl2, Cl2O2, ClOO, ClNO2, ClNO3, 
         CCl4, CFCs, CH3Cl, CH2Cl2, CH3CCl3, CHCl3, HOCl, HCl, Halons, HCFCs, OClO   
      Iodine: Iy, IxOy, I, I2, IBr, ICl, IO, ION, IONO2, CH3I, CH2I2,
         CH2ICl, CH2IBr, HI, HOI, OIO
      Nitrogen: NOy, NOx, HNO2, HNO3, HNO4, MPAN, NIT, 'NO', NO2, NO3,
          N2O5, MPN, PAN, PPN, N2O, NHx, NH3, NH4, MENO3, ETNO3, IPRNO3, NPRNO3
      Oxidants: O3, CO, OH, NOx   
      Primary_Organics:
         Alcohols: EOH, MOH
         Biogenics: ISOP, MTPA, MTPO, LIMO
         HCs: ALK4, BENZ, CH4, C2H6, C3H8, PRPE, TOLU, XYLE
         ROy: H2O2, H, H2, H2O, HO2, O1D, OH, RO2
      Secondary_Organic_Aerosols:
         Complex_SOA: TSOA0, TSOA1, TSOA2, TSOA3, ASOA1, ASOA2, ASOA3,
             ASOAN, TSOG0, TSOG1, TSOG2, TSOG3, ASOG1, ASOG2, ASOG3
         Isoprene_SOA: INDIOL, LVOCOA, SOAIE, SOAGX
         Simple_SOA: SOAP, SOAS
      Secondary_Organics:
         Acids: ACTA
         Aldehydes: ALD2, CH2O, HPALDs, MACR
         Epoxides: IEPOX
         Ketones: ACET, MEK, MVK
         Nitrates: ISOPN
         Other: GLYX, HCOOH, MAP, RCHO
         Peroxides: MP
      Sulfur: SOx, DMS, OCS, SO2, SO4
   TransportTracersBenchmark:
      RnPbBeTracers: Rn222, Pb210, Pb210Strat, Be7, Be7Strat, Be10, Be10Strat
      PassiveTracers: PassiveTracer, SF6Tracer, CH3ITracer, COAnthroEmis25dayTracer,
          COAnthroEmis50dayTracer, COUniformEmis25dayTracer, GlobEmis90dayTracer,
          NHEmis90dayTracer, SHEmis90dayTracer

   """



make_benchmark_emis_plots
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def make_benchmark_emis_plots(ref, refstr, dev, devstr, dst="./benchmark",
      subdst=None, plot_by_spc_cat=False, plot_by_hco_cat=False, overwrite=False,
      verbose=False,   flip_ref=False, flip_dev=False, log_color_scale=False,
      sigdiff_files=None, weightsdir='.', n_job=-1, spcdb_dir=os.path.dirname(__file__)
   ):
      """
      Creates PDF files containing plots of emissions for model
      benchmarking purposes. This function is compatible with benchmark
      simulation output only. It is not compatible with transport tracers
      emissions diagnostics.

   Remarks:
      --------
         (1) If both plot_by_spc_cat and plot_by_hco_cat are
            False, then all emission plots will be placed into the
            same PDF file.

         (2) Emissions that are 3-dimensional will be plotted as
            column sums.
      """

Function-specific keyword args:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: plot_by_spc_cat : bool
         
      Set this flag to True to separate plots into PDF files
         according to the benchmark species categories (e.g. Oxidants,
         Aerosols, Nitrogen, etc.)  These categories are specified
         in the YAML file benchmark_species.yml.

         Default value: False

.. option:: plot_by_hco_cat : bool

   Set this flag to True to separate plots into PDF files
   according to HEMCO emissions categories (e.g. Anthro,
   Aircraft, Bioburn, etc.)

   Default value: False

.. option:: flip_ref : bool

   Set this flag to True to reverse the vertical level
   ordering in the "Ref" dataset (in case "Ref" starts
   from the top of atmosphere instead of the surface).

   Default value: False

.. option:: flip_dev : bool

   Set this flag to True to reverse the vertical level
   ordering in the "Dev" dataset (in case "Dev" starts
   from the top of atmosphere instead of the surface).

   Default value: False


This function generates plots of total emissions using output from ``HEMCO_diagnostics`` (for GEOS-Chem Classic) and/or ``GCHP.Emissions`` output files.


make_benchmark_jvalue_plots
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def make_benchmark_jvalue_plots(ref, refstr, dev, devstr, varlist=None,
         dst="./benchmark", subdst=None, local_noon_jvalues=False, 
         plots=["sfc", "500hpa", "zonalmean"],overwrite=False, verbose=False,
         flip_ref=False, flip_dev=False, log_color_scale=False, sigdiff_files=None,
         weightsdir='.', n_job=-1, spcdb_dir=os.path.dirname(__file__)
   ):
      """
      Creates PDF files containing plots of J-values for model
      benchmarking purposes.

      Remarks:
      --------
          Will create 4 files containing J-value plots:
            (1 ) Surface values
            (2 ) 500 hPa values
            (3a) Full-column zonal mean values.
            (3b) Stratospheric zonal mean values
          These can be toggled on/off with the plots keyword argument.

          At present, we do not yet have the capability to split the
          plots up into separate files per category (e.g. Oxidants,
          Aerosols, etc.).  This is primarily due to the fact that
          we archive J-values from GEOS-Chem for individual species
          but not family species.  We could attempt to add this
          functionality later if there is sufficient demand.
      """


Function-specific keyword args:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: varlist : list of str

   List of J-value variables to plot.  If not passed,
   then all J-value variables common to both dev
   and ref will be plotted.  The varlist argument can be
   a useful way of restricting the number of variables
   plotted to the pdf file when debugging.

   Default value: None

.. option:: local_noon_jvalues : bool

   Set this flag to plot local noon J-values.  This will
   divide all J-value variables by the JNoonFrac counter,
   which is the fraction of the time that it was local noon
   at each location.

   Default value: False

.. option:: plots : list of strings

   List of plot types to create.

   Default value: ['sfc', '500hpa', 'zonalmean']

.. option:: flip_ref : bool

   Set this flag to True to reverse the vertical level
   ordering in the "Ref" dataset (in case "Ref" starts
   from the top of atmosphere instead of the surface).

   Default value: False

.. option:: flip_dev : bool

   Set this flag to True to reverse the vertical level
   ordering in the "Dev" dataset (in case "Dev" starts
   from the top of atmosphere instead of the surface).

   Default value: False


This function generates plots of J-values using the ``JValues`` GEOS-Chem output files. 

make_benchmark_wetdep_plots
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def make_benchmark_wetdep_plots(ref, refstr, dev, devstr, collection,
         dst="./benchmark", datestr=None, overwrite=False, verbose=False,
         benchmark_type="TransportTracersBenchmark", plots=["sfc", "500hpa", "zonalmean"],
         log_color_scale=False, normalize_by_area=False, areas=None, refmet=None,
         devmet=None, weightsdir='.', n_job=-1, spcdb_dir=os.path.dirname(__file__)
   ):
      """
      Creates PDF files containing plots of species concentration
      for model benchmarking purposes.
   """


Function-specific keyword args:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. option:: datestr : str

   A string with date information to be included in both the
   plot pdf filename and as a destination folder subdirectory
   for writing plots

   Default value: None

.. option:: benchmark_type: str

   A string denoting the type of benchmark output to plot,
   either FullChemBenchmark or TransportTracersBenchmark. 

   Default value: "FullChemBenchmark"

.. option:: plots : list of strings

   List of plot types to create.

   Default value: ['sfc', '500hpa', 'zonalmean']

.. option:: normalize_by_area: bool

   Set this flag to true to enable normalization of data
   by surfacea area (i.e. kg s-1 --> kg s-1 m-2).

     Default value: False

.. option:: areas : dict of xarray DataArray:

   Grid box surface areas in m2 on Ref and Dev grids.

   Default value: None

.. option:: refmet : str

   Path name for ref meteorology

   Default value: None

.. option:: devmet : str

   Path name for dev meteorology  

   Default value: None


      
This function generates plots of wet deposition using ``WetLossConv`` and ``WetLossLS`` GEOS-Chem output files.
It is currently primarily used for 1-Year Transport Tracer benchmarks, plotting values for the following species as defined in ``benchmark_categories.yml``:

.. code-block:: python

   """
      WetLossConv: Pb210, Pb210Strat, Be7, Be7Strat, Be10, Be10Strat
      WetLossLS: Pb210, Pb210Strat, Be7, Be7Strat, Be10, Be10Strat
   """