"""GeoJSON Parser used plot_collections upload"""

import json
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile
from geoalchemy2.elements import WKTElement
from shapely.geometry import Polygon, shape
from sqlmodel import Session, select

from src.data_upload import apply_rows, commit_or_conflict
from src.models.base import UploadModes
from src.models.registry import ManagedTables
from src.models.tables.plot import Plot, PlotDelete, PlotInsert
from src.models.upload_models import PlotCollectionUpload

SRID_REQUIRED = 2056


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
                "mode": "insert",  # feature rows are always inserts of the (new/replacement)
                # plot set — one file always represents the whole plot set; the
                # file's own mode lives in the header and governs the collection
                # record (update = delete whole set + reinsert; delete = clear)
                # and the plot_collection id
                "label": properties.get("id"),  # id cannot be used in database --> rename to label
                "row": properties.get("row"),
                "col": properties.get("col"),
                "geometry": feature.get("geometry"),
            }
        )
    features_df = pd.DataFrame(
        records, columns=["mode", "label", "row", "col", "geometry"]
    )

    mode_raw = parsed.get("mode")
    header_df = pd.DataFrame(
        [
            {
                "id": parsed.get("id"),
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


def _derive_plot_delete_records(
    session: Session, collection_id: int
) -> list[PlotDelete]:
    """Derive delete records for every existing plot of a collection.

    Plot ids are DB-borne (files don't carry them); the derivation turns them
    into apply_rows-shaped DELETE records so the plot batch behaves like any
    other table's delete rows.
    """
    plot_ids = session.exec(
        select(Plot.id).where(Plot.plot_collection_id == collection_id)
    ).all()
    return [PlotDelete(id=plot_id, mode="delete") for plot_id in plot_ids]


def _geojson_to_wkt(geometry: dict[str, Any]) -> WKTElement:
    """Normalize a raw GeoJSON geometry into a PostGIS-bound WKT element."""
    try:
        polygon = shape(geometry)
    except (TypeError, ValueError) as err:
        raise HTTPException(
            status_code=422, detail=f"Invalid geometry: {err}"
        ) from err
    if not isinstance(polygon, Polygon):
        raise HTTPException(
            status_code=422,
            detail="Only Polygon geometries are supported, got "
            f"{geometry.get('type')!r}.",
        )
    return WKTElement(polygon.wkt, srid=SRID_REQUIRED)


def apply_plot_collection(
    session: Session,
    header_record: PlotCollectionUpload,
    plot_records: list[PlotInsert],
) -> None:
    """Write the validated aggregate in ONE transaction via the shared row engine.

    The file represents its plot_collection plus the whole plot set: update
    deletes and reinserts the set (only the collection row and its id
    survive); delete clears everything; insert creates both. Every plot
    batch goes through apply_rows exactly like every other table.
    """
    if header_record.mode == UploadModes.DELETE:
        apply_rows(
            session,
            ManagedTables.PLOT,
            _derive_plot_delete_records(session, header_record.id),
        )
        apply_rows(session, ManagedTables.PLOT_COLLECTION, [header_record])
    else:  # INSERT / UPDATE
        if header_record.mode == UploadModes.UPDATE:
            apply_rows(
                session,
                ManagedTables.PLOT,
                _derive_plot_delete_records(session, header_record.id),
            )
        collection = apply_rows(
            session, ManagedTables.PLOT_COLLECTION, [header_record]
        )[0]
        for record in plot_records:
            record.plot_collection_id = collection.id
            record.geometry = _geojson_to_wkt(record.geometry)
        apply_rows(session, ManagedTables.PLOT, plot_records)

    commit_or_conflict(session)
