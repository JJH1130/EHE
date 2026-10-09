# Analysis scripts

Pure-Python / Node scripts developed for the MAUP bias analysis in the EHE
(폭염 노출) exposure-projection paper. No GIS libraries (rasterio, gdal,
geopandas, pysal/esda, pyshp) were available in the environment these were
written in, so TIFF decoding, shapefile I/O, and Local Moran's I are all
implemented from scratch in NumPy/SciPy/struct.

## `decomposition/`
- `lzw_tiff.py` — pure-Python LZW TIFF decoder for the heatdays rasters.
- `resample_and_decompose.py` — resamples population/heatdays rasters to a
  common 1 km grid.
- `decomposition_analysis.py` / `decomposition_analysis_colab.py` —
  shift-share decomposition of the 2030→2060 change in exposure
  (climate / population / interaction effects), at grid, municipal, and
  provincial scales. Source of Table 1 (the −12.5% / −13.9% bias figures).

## `covariance_point_analysis/`
- `read_points.py` — pure-Python ESRI shapefile (Point type) + DBF reader.
- `covariance_analysis.py` — computes per-province Cov(population,
  heatdays) for 2030/2060 from the 500 m point layer.
- `make_scatter.py` — covariance-vs-relative-bias scatter plot (exploratory;
  not used in the final paper).

## `lisa_sensitivity/`
Grid-level Local Moran's I (LISA), implemented via sparse K-NN / distance-
band weight matrices and conditional-permutation significance testing
(global shuffle + sparse matvec — fast, large-n-standard approximation of
esda/GeoDa's conditional permutation).
- `grid_lisa.py` — first-pass implementation (free-sampling permutation
  null; superseded by the sparse approach below).
- `distance_band_lisa.py` — introduces `local_moran_sparse()`, Euclidean
  distance-band weights, and the K-NN vs. distance-band comparison.
- `fine_sensitivity_2030.py` — main sensitivity sweep: K = {4,8,12,16,24}
  and distance bands = {500,1000,1500,2000} m, all at p≤0.001, 2030 only.
  Produces one titled PNG per setting.
- `threshold_sweep.py` — same weight schemes at K:4 / 500 m / 1000 m,
  each at p ≤ {0.05, 0.01, 0.001}.
- `shp_writer.py` — pure-Python ESRI Shapefile (Point) + DBF + PRJ writer.
- `export_shp.py` — recomputes the K:4 and distance-band:1000 m (p≤0.001)
  LISA results and exports them as point shapefiles (CRS: KGD2002) for
  independent verification in ArcGIS Pro.

## `docx_tables/`
Node (`docx` package) scripts generating journal-style three-line tables
as `.docx` files. `build_table_cov.js` is the per-province covariance /
provincial-bias table (exploratory; not used in the final paper). The
others (`build_table.js`–`build_table5.js`) are earlier drafts of the
paper's main results tables.
