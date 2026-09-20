<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { TrailFeature } from '$lib/types';

  export let trail: TrailFeature;

  let container: HTMLDivElement;
  let mapInstance: any = null;

  const difficultyColor: Record<string, string> = {
    T:   '#52b788',
    E:   '#2d6a4f',
    EE:  '#e9c46a',
    EEA: '#e63946',
  };

  onMount(async () => {
    if (typeof window === 'undefined') return;

    const { default: maplibregl } = await import('maplibre-gl');
    await import('maplibre-gl/dist/maplibre-gl.css');

    const coords = trail.geometry.coordinates as [number, number][];
    const start  = coords[0];
    const end    = coords[coords.length - 1];

    // Compute bounding box
    let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
    for (const [lng, lat] of coords) {
      if (lng < minLng) minLng = lng;
      if (lat < minLat) minLat = lat;
      if (lng > maxLng) maxLng = lng;
      if (lat > maxLat) maxLat = lat;
    }

    mapInstance = new maplibregl.Map({
      container,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm-tiles',
          },
        ],
      },
      interactive: false,
      attributionControl: false,
    });

    mapInstance.on('load', () => {
      if (!mapInstance) return; // guard against unmount during async load
      const lineColor = difficultyColor[trail.properties.difficulty ?? 'E'] ?? '#2d6a4f';

      mapInstance.addSource('trail-line', {
        type: 'geojson',
        data: trail,
      });

      mapInstance.addLayer({
        id: 'trail-line',
        type: 'line',
        source: 'trail-line',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': lineColor,
          'line-width': 3,
        },
      });

      // Start point (green circle)
      mapInstance.addSource('start-point', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: start },
          properties: {},
        },
      });

      mapInstance.addLayer({
        id: 'start-point',
        type: 'circle',
        source: 'start-point',
        paint: {
          'circle-radius': 7,
          'circle-color': '#52b788',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      });

      // End point (red circle)
      mapInstance.addSource('end-point', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: end },
          properties: {},
        },
      });

      mapInstance.addLayer({
        id: 'end-point',
        type: 'circle',
        source: 'end-point',
        paint: {
          'circle-radius': 7,
          'circle-color': '#e63946',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      });

      mapInstance.fitBounds(
        [[minLng, minLat], [maxLng, maxLat]],
        { padding: 40, animate: false }
      );
    });
  });

  onDestroy(() => {
    if (mapInstance) {
      const m = mapInstance;
      mapInstance = null; // nullify before remove to prevent post-destroy callbacks
      m.remove();
    }
  });
</script>

<div class="trail-map" bind:this={container}></div>

<style>
  .trail-map {
    width: 100%;
    height: 300px;
    border-radius: var(--radius-md);
    overflow: hidden;
  }
</style>
