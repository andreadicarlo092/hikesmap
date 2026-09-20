/**
 * Trail Explorer — API client
 *
 * All functions use the native fetch API.
 * Base URL is read from the SvelteKit public env variable PUBLIC_API_URL.
 * On error, an Error is thrown with a descriptive message.
 */

import { env } from '$env/dynamic/public';
import type { Trail, ElevationProfile, TrailFeature } from './types';

function baseUrl(): string {
  const url = env.PUBLIC_API_URL ?? '';
  if (!url) {
    throw new Error('PUBLIC_API_URL is not set. Check your .env file.');
  }
  return url.replace(/\/$/, '');
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status} on ${path}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Fetch all trailheads within a bounding box.
 * @param bbox [west, south, east, north] in WGS-84 decimal degrees
 */
export function fetchTrailheads(
  bbox: [number, number, number, number]
): Promise<GeoJSON.FeatureCollection> {
  const [west, south, east, north] = bbox;
  return apiFetch<GeoJSON.FeatureCollection>(
    `/api/v1/trailheads?bbox=${west},${south},${east},${north}`
  );
}

/**
 * Fetch the list of trails departing from a given trailhead.
 * @param id Trailhead numeric ID
 */
export function fetchTrailheadTrails(id: number): Promise<Trail[]> {
  return apiFetch<Trail[]>(`/api/v1/trailheads/${id}/trails`);
}

/**
 * Fetch the full detail of a single trail (with GeoJSON geometry).
 * @param id Trail numeric ID
 */
export function fetchTrail(id: number): Promise<TrailFeature> {
  return apiFetch<TrailFeature>(`/api/v1/trails/${id}`);
}

/**
 * Fetch the elevation profile for a trail.
 * Returns null if the trail has no elevation data (404).
 * @param id Trail numeric ID
 */
export async function fetchElevationProfile(id: number): Promise<ElevationProfile | null> {
  const url = `${baseUrl()}/api/v1/trails/${id}/elevation`;
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new Error(`API error ${res.status} on /api/v1/trails/${id}/elevation: ${await res.text()}`);
  }
  return res.json() as Promise<ElevationProfile>;
}

/** GeoJSON FeatureCollection con geometria semplificata del sentiero + bbox opzionale */
export interface TrailGeometryCollection extends GeoJSON.FeatureCollection {
  bbox?: [number, number, number, number];
}

/**
 * Fetch simplified geometry for a trail (for map rendering).
 * @param id Trail numeric ID
 */
export function fetchTrailGeometry(id: number): Promise<TrailGeometryCollection> {
  return apiFetch<TrailGeometryCollection>(`/api/v1/trails/${id}/geometry`);
}
