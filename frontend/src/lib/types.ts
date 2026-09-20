/**
 * Trail Explorer — shared TypeScript interfaces
 */

/** CAI difficulty scale */
export type Difficulty = 'T' | 'E' | 'EE' | 'EEA';

/** Core trail metadata (returned by list endpoints and embedded in TrailFeature) */
export interface Trail {
  id: number;
  name: string;
  /** CAI route reference, e.g. "101" */
  cai_ref?: string | null;
  difficulty?: Difficulty | null;
  length_km?: number | null;
  elevation_gain_m?: number | null;
  elevation_loss_m?: number | null;
  /** Estimated walking duration in hours */
  duration_hours?: number | null;
  tags?: string[] | null;
  /** OpenStreetMap relation URL */
  osm_url?: string | null;
}

/**
 * Properties inside a GeoJSON Feature from the trailhead list endpoint.
 * Corresponds to GET /api/v1/trailheads (FeatureCollection).
 */
export interface TrailheadProperties {
  id: number;
  name: string;
  /** Number of trails starting from this trailhead */
  trail_count: number;
}

/**
 * Full trailhead detail returned by GET /api/v1/trailheads/{id}.
 * Position is provided as separate lat/lon fields, not as a coordinates array.
 */
export interface TrailheadDetail {
  id: number;
  name: string;
  trail_count: number;
  lat: number;
  lon: number;
}

/** One sample of the elevation profile */
export interface ElevationSample {
  /** Distance from start in kilometres */
  d_km: number;
  /** Altitude in metres above sea level */
  alt_m: number;
}

/** Full elevation profile for a trail */
export interface ElevationProfile {
  /** Array of distance/altitude samples */
  profile: ElevationSample[];
  gain_m: number;
  loss_m: number;
  max_alt_m: number;
  min_alt_m: number;
}

/** GeoJSON Feature wrapping a trail's LineString geometry + Trail properties */
export interface TrailFeature extends GeoJSON.Feature<GeoJSON.LineString, Trail> {
  type: 'Feature';
}
