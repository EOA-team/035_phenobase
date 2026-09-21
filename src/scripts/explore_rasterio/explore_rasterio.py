from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
from matplotlib import pyplot as plt
import hvplot.xarray 
import panel as pn


def fetch_wavelengths(da: xr.DataArray) -> np.ndarray:
    """Wavelengths (nm) per band, from the mosaic's long_name attribute."""
    names = da.attrs["long_name"]
    wl = np.array([float(s.rsplit("(", 1)[-1].rstrip(")")) for s in names])
    return wl


def load_orthomosaic(filepath: Path) -> xr.DataArray:
    """Load an orthomosaic GeoTIFF as an xarray DataArray
    and assign wavelengths"""
    tmp_da = rioxarray.open_rasterio(filepath, masked=True, chunks=True)
    new_da = tmp_da.assign_coords(wavelength=("band", fetch_wavelengths(tmp_da)))
    return new_da


def extract_spectruma_at_pixel(da: xr.DataArray, ix: int, iy: int) -> xr.DataArray:
    """Extract the spectrum at a given pixel indices (x, y) coordinte from the orthomosaic DataArray."""
    # Use nearest neighbor selection to get the spectrum at the specified coordinates
    spectrum = da.isel(x=ix, y=iy)
    return spectrum


def plot_spectrum_at_pixel(da: xr.DataArray, ix: int, iy: int, filepath: Path):
    """Plot the reflectance spectrum at a given pixel indices (x, y) coordinate."""
    spectrum = extract_spectruma_at_pixel(da, ix, iy)
    y_values = spectrum.values
    x_values = spectrum.coords["wavelength"].values

    plt.figure(figsize=(10, 5))
    plt.plot(x_values, y_values)
    plt.title(f"Reflectance Spectrum at Pixel Coordinates (x={ix}, y={iy})")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.savefig(filepath)


if __name__ == "__main__":
    filename = Path(__file__).parent / "mosaic_reflectance.tif"
    da = load_orthomosaic(filepath=filename)
    plot_spectrum_at_pixel(
        da, ix=100, iy=200, filepath=Path(__file__).parent / "spectrum_plot.png"
    )  

    b550 = da.sel(wavelength=550, method="nearest")
    b550.plot.imshow(cmap="gray", robust=True)
    plt.savefig(Path(__file__).parent / "band_550_plot.png")


    reflectance = da
    browser= reflectance.hvplot.image(
         x="x", y="y", groupby="band",     # <- slider over all 487 bands
         cmap="gray", robust=True,
         widget_type="scrubber", widget_location="bottom",
         framewise =False,
         width=1400, height=700,
     )
    pn.serve(browser, title="Orthomosaic Reflectance Browser", port=5006, show=True)




    # spec.sel(wavelength=slice(400,1000)).plot.line(x="wavelength", y="band", hue="band", marker="o")
    # b1 = da.sel(band=1)
