"""Extract the traits L_in and L_out of a radiance orthomosaic for the 3FLD method (Maier et al. 2003).

L_in : Radiance at the absorption band (762.506270 nm)
L_out: Linear interpolation of the left (753.784460 nm) and right shoulder(771.228080 nm) bands

Note: L_out is the average of the left and right shoulder bands ,
because they have same distance to the absorption band (762.506270 nm) and are therefore weighted equally.

The final SIF (Solar Induced Fluorescence) can be calcultaed after selecting a non-fluorescent reference
polygon (e.g. a street) and then inside the reference polygon "k" can be estimated:

k  = mean(L_in) / mean(L_out)

With "k" known the following Formula can be applied on the whole orthomosaic to Calculate the SIF:
SIF = (L_in - k * L_out) / (1 - k)
"""

from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
from matplotlib import pyplot as plt


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


def extract_3fld_traits(da: xr.DataArray) -> xr.DataArray:
    """Extract the Radiance at the absorption band (762.506270 nm) as a trait "Lin"""
    wl_in = 762.506270
    wl_left = 753.784460
    wl_right = 771.228080
    l_in = da.sel(wavelength=wl_in, method="nearest")
    l_left = da.sel(wavelength=wl_left, method="nearest")
    l_right = da.sel(wavelength=wl_right, method="nearest")

    l_out = (l_left + l_right) / 2
    return l_in, l_out


def save_traits(l_in: xr.DataArray, l_out: xr.DataArray, filepath: Path):
    # Drop wavelength and band labeldata
    l_in = l_in.drop_vars(["band", "wavelength"], errors="ignore")
    l_out = l_out.drop_vars(
        ["band", "wavelength"], errors="ignore"
    )  # should be dropped already, but just in case

    # Drop existing metadata attributes to avoid conflicts when saving to raster
    l_in.attrs = {}
    l_out.attrs = {}

    # Stack traits to 2-band DataArray
    traits = xr.concat(
        [l_in, l_out],
        dim=xr.DataArray(["L_in", "L_out"], dims="band", name="band"),
    )

    traits.attrs["long_name"] = ("L_in", "L_out")

    traits.rio.to_raster(filepath, dtype="float32", nodata=np.nan)


def load_traits(filepath: Path) -> xr.DataArray:
    """Load traits GeoTIFF and restore L_in/L_out band labels from long_name."""
    da = rioxarray.open_rasterio(filepath, masked=True)
    names = da.attrs.get("long_name")
    da = da.assign_coords(band=("band", np.asarray(names, dtype=str)))
    return da


if __name__ == "__main__":
    input_file = Path(__file__).parent / "mosaic_radiance.tif"
    output_file = Path(__file__).parent / "mosaic_3fld_traits.tif"
    da_in = load_orthomosaic(filepath=input_file)
    l_in, l_out = extract_3fld_traits(da_in)
    save_traits(l_in, l_out, filepath=output_file)

    da_out = load_traits(filepath=output_file)

    da_out.sel(band="L_in").plot.imshow(cmap="gray", robust=True)
    plt.savefig(Path(__file__).parent / "L_in.png")

    da_out.sel(band="L_out").plot.imshow(cmap="gray", robust=True)
    plt.savefig(Path(__file__).parent / "L_out.png")

    print(da_in.sel(wavelength=762.506270).isel(x=1000, y=1000).values)

    print("expected L_out value:", da_out.sel(band="L_out").isel(x=1000, y=1000).values)

    left_shoulder = (
        da_in.sel(wavelength=753.784460, method="nearest").isel(x=1000, y=1000).values
    )
    right_shoulder = (
        da_in.sel(wavelength=771.228080, method="nearest").isel(x=1000, y=1000).values
    )
    l_out = (left_shoulder + right_shoulder) / 2

    print("calculated L_out value:", l_out)
