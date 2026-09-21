"""
This is a workaround to prevent rasterio import issues
on the Drone Station.

More Info: https://github.com/EOA-team/035_phenobase/issues/14
"""

import os

os.environ["PATH"] = os.pathsep.join(
    p for p in os.environ["PATH"].split(os.pathsep) if "MATLAB Runtime" not in p
)
