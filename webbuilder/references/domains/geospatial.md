# Geospatial Domain Reference

> **Scope** — This reference defines domain conventions and constraints for
> geospatial web applications built with WebBuilder.  It is consumed by the
> evaluation pipeline and does **not** imply ownership of implementation by
> any single contributor or team.

## Coordinate Systems

- WGS 84 (EPSG:4326) is the canonical storage coordinate reference system.
- Display layers SHOULD support Web Mercator (EPSG:3857) for tile compatibility.
- Coordinate pairs MUST be expressed as `[longitude, latitude]` in GeoJSON.

## Tile Rendering

- Vector tiles (MVT) are preferred over raster tiles for interactive maps.
- Tile pyramid MUST follow the Slippy Map tiling scheme (z/x/y).
- Tile caching SHOULD use HTTP cache headers with a minimum max-age of 300 s.

## Spatial Queries

- Spatial indices MUST be created on geometry columns before querying.
- Bounding-box queries MUST use the spatial index and reject full table scans.
- Distance calculations MUST use geodesic math (Haversine or Vincenty), not
  planar Euclidean distance, for results at or above 1 km.

## Layer Management

- The application MUST support toggling at least three independent map layers.
- Layer ordering MUST be user-configurable via drag-and-drop or equivalent.
- Each layer MUST carry human-readable metadata (title, description, source).

## Performance Budgets

- Initial map render MUST complete within 2 s on a 4G connection.
- Tile requests MUST return within 500 ms (p95) under nominal load.
- Spatial queries covering up to 100 k features MUST return within 1 s.

## Accessibility

- Map controls MUST be keyboard-navigable.
- Alternative text descriptions MUST be available for rendered map views.
- High-contrast mode MUST be supported for all overlay elements.

## Security

- GeoJSON uploads MUST be validated against the GeoJSON schema before storage.
- Spatial data access MUST respect per-user permission boundaries.
- Tile endpoints MUST NOT expose data beyond the authenticated user's scope.

## Non-Ownership Statement

This reference is a shared specification maintained collaboratively.  No
individual, team, or organization owns exclusive rights to the geospatial
domain conventions defined herein.  All contributors are expected to follow
these conventions when building geospatial applications with WebBuilder.
