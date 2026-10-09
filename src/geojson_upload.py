import json

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from src.models.tables.plot_collection import PlotCollection


def _extract_crs(parsed: dict) -> str | None:
    """Extract a CRS string from the GeoJSON header, whatever its shape."""
    crs = parsed.get("crs")
    if isinstance(crs, dict):
        properties = crs.get("properties")
        if isinstance(properties, dict) and isinstance(properties.get("name"), str):
            return properties["name"]
    if isinstance(crs, str):
        return crs
    return None


def read_plot_collection(upload_file: UploadFile) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse the GeoJSON file into two dataframes: "header_df" refers to the plot collection (one or zero rows for insert/update/delete mode) and "plot_df" contains the plots (one row per plot/feature)."""
    raw = upload_file.file.read()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as err:
        raise HTTPException(
            status_code=422, detail=f"Malformed GeoJSON: {err}"
        ) from err
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=422,
            detail="Malformed GeoJSON: expected a FeatureCollection object.",
        )
    features = parsed.get("features")
    if not isinstance(features, list):
        raise HTTPException(
            status_code=422, detail="Malformed GeoJSON: missing 'features' array."
        )

    records = []
    for feature in features:
        properties = feature.get("properties", {}) if isinstance(feature, dict) else {}
        properties = properties if isinstance(properties, dict) else {}
        records.append(
            {
                "label": properties.get("id"),  # id cannot be used in database --> rename to label
                "row": properties.get("row"),
                "col": properties.get("col"),
                "geometry": feature.get("geometry"),
            }
        )
    features_df = pd.DataFrame(records, columns=["label", "row", "col", "geometry"])

    mode_raw = parsed.get("mode")
    header_df = pd.DataFrame(
        [
            {
                "mode": str(mode_raw).strip().lower() if isinstance(mode_raw, str) else None,
                "name": parsed.get("name"),
                "category": parsed.get("category"),
                "crs": _extract_crs(parsed),
            }
        ]
    )

    # Mirror read_upload_file's normalization: pandas NaN/None markers → None,
    # so the shared validator sees consistent Python values.
    features_df = features_df.replace({pd.NA: None, float("nan"): None})
    header_df = header_df.replace({pd.NA: None, float("nan"): None})

    return header_df, features_df


def resolve_plot_collection_id(session: Session, name: str) -> int:
    """Resolve a human-readable collection name to its surrogate id.

    This is the embryonic resolver for update/delete targets: seeds address
    rows by NAME while the tables connect via ids. Raises 422 when the
    collection does not exist.
    """
    collection_id = session.exec(
        select(PlotCollection.id).where(PlotCollection.name == name)
    ).first()
    if collection_id is None:
        raise HTTPException(
            status_code=422,
            detail=f"Plot collection '{name}' does not exist (required for update/delete).",
        )
    return collection_id
