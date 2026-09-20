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
  cai_ref: string;
  difficulty: Difficulty;
  length_km: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  /** Estimated walking duration in hours */
  duration_hours: number;
  tags: string[];
}

/** Summary info for a trailhead (departure point for one or more trails) */
export interface Trailhead {
  id: number;
  name: string;
  /** Number of trails starting from this trailhead */
  trail_count: number;
  /** [longitude, latitude] in WGS-84 */
  coordinates: [number, number];
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
