<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { browser } from '$app/environment';

  export let selectedTrailId: number | null = null;

  const dispatch = createEventDispatcher<{ trailheadClick: { id: number } }>();

  let mapContainer: HTMLDivElement;
  let map: any = null;
  let maplibregl: any = null;

  const TRAILHEAD_SOURCE = 'trailheads';
  const TRAIL_LINE_SOURCE = 'selected-trail';

  const DIFFICULTY_COLORS: Record<string, string> = {
    T: '#52b788',
    E: '#2d6a4f',
    EE: '#e9c46a',
    EEA: '#e63946',
  };

  // Dynamic import guard — only runs in browser
  async function initMap() {
    if (!browser) return;

    const [mgl, { Protocol }] = await Promise.all([
      import('maplibre-gl'),
      import('pmtiles'),
    ]);
    maplibregl = mgl.default ?? mgl;
    const protocol = new Protocol();
    maplibregl.addProtocol('pmtiles', protocol.tile.bind(protocol));

    map = new maplibregl.Map({
      container: mapContainer,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [10.5, 45.5],
      zoom: 7,
      attributionControl: true,
    });

    map.on('load', () => {
      addTrailheadSource();
      addTrailheadLayers();
      addTrailLineSource();
      addTrailLineLayer();
      bindEvents();
      // Apply selectedTrailId that may have been set before map was ready
      if (selectedTrailId != null) {
        updateSelectedTrail(selectedTrailId);
      }
    });

    map.on('moveend', () => {
      if (!hasVectorSource()) {
        loadTrailheadsGeoJSON();
      }
    });
  }

  function hasVectorSource(): boolean {
    const pmtilesUrl = typeof window !== 'undefined'
      ? (window as any).__env?.PUBLIC_TRAILHEADS_PMTILES
      : undefined;
    return !!pmtilesUrl;
  }

  function trailheadsSourceUrl(): string | null {
    if (typeof window !== 'undefined') {
      const pmtiles = (window as any).__env?.PUBLIC_TRAILHEADS_PMTILES;
      if (pmtiles) return `pmtiles://${pmtiles}`;
    }
    return null;
  }

  function addTrailheadSource() {
    const pmtilesUrl = trailheadsSourceUrl();
    if (pmtilesUrl) {
      map.addSource(TRAILHEAD_SOURCE, {
        type: 'vector',
        url: pmtilesUrl,
      });
    } else {
      // Fallback: GeoJSON from API, will be populated on moveend
      map.addSource(TRAILHEAD_SOURCE, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
        cluster: true,
        clusterMaxZoom: 12,
        clusterRadius: 50,
      });
      loadTrailheadsGeoJSON();
    }
  }

  async function loadTrailheadsGeoJSON() {
    if (!map) return;
    const bounds = map.getBounds();
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
    try {
      const res = await fetch(`/api/v1/trailheads?bbox=${bbox}`);
      if (!res.ok) return;
      const data = await res.json();
      const src = map.getSource(TRAILHEAD_SOURCE);
      if (src) src.setData(data);
    } catch (_) {
      // network error — silently ignore
    }
  }

  function addTrailheadLayers() {
    const isPmtiles = !!trailheadsSourceUrl();
    const sourceLayer = isPmtiles ? 'trailheads' : undefined;

    // Cluster circles (GeoJSON clustering only)
    if (!isPmtiles) {
      map.addLayer({
        id: 'trailheads-clusters',
        type: 'circle',
        source: TRAILHEAD_SOURCE,
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': '#e9c46a',
          'circle-radius': ['interpolate', ['linear'], ['get', 'point_count'], 2, 16, 10, 28],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
        },
      });

      map.addLayer({
        id: 'trailheads-cluster-count',
        type: 'symbol',
        source: TRAILHEAD_SOURCE,
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          'text-size': 13,
        },
        paint: {
          'text-color': '#1a1a2e',
        },
      });
    }

    // Individual trailhead circles
    const circleLayerSpec: any = {
      id: 'trailheads-circles',
      type: 'circle',
      source: TRAILHEAD_SOURCE,
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 5, 14, 12],
        'circle-color': '#2d6a4f',
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff',
      },
    };
    if (sourceLayer) circleLayerSpec['source-layer'] = sourceLayer;
    if (!isPmtiles) circleLayerSpec.filter = ['!', ['has', 'point_count']];
    map.addLayer(circleLayerSpec);
  }

  function addTrailLineSource() {
    map.addSource(TRAIL_LINE_SOURCE, {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] },
    });
  }

  function addTrailLineLayer() {
    map.addLayer({
      id: 'trails-line',
      type: 'line',
      source: TRAIL_LINE_SOURCE,
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-width': 3,
        'line-color': [
          'match',
          ['get', 'difficulty'],
          'T', '#52b788',
          'E', '#2d6a4f',
          'EE', '#e9c46a',
          'EEA', '#e63946',
          '#52b788',
        ],
      },
    });
  }

  function bindEvents() {
    // Click on individual trailhead — dispatch Svelte event
    map.on('click', 'trailheads-circles', (e: any) => {
      const feature = e.features?.[0];
      if (!feature) return;
      const id = feature.properties?.id;
      if (id != null) dispatch('trailheadClick', { id: Number(id) });
    });

    // Click on cluster → zoom in
    map.on('click', 'trailheads-clusters', (e: any) => {
      const feature = e.features?.[0];
      if (!feature) return;
      const clusterId = feature.properties?.cluster_id;
      const src = map.getSource(TRAILHEAD_SOURCE) as any;
      src.getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
        if (err) return;
        map.flyTo({ center: feature.geometry.coordinates, zoom: zoom + 2 });
      });
    });

    // Pointer cursor on hover
    map.on('mouseenter', 'trailheads-circles', () => {
      map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'trailheads-circles', () => {
      map.getCanvas().style.cursor = '';
    });
    if (map.getLayer('trailheads-clusters')) {
      map.on('mouseenter', 'trailheads-clusters', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'trailheads-clusters', () => {
        map.getCanvas().style.cursor = '';
      });
    }
  }

  // Reactive: update trail line when selectedTrailId changes
  $: if (map && map.isStyleLoaded()) {
    updateSelectedTrail(selectedTrailId);
  }

  async function updateSelectedTrail(trailId: number | null) {
    if (!map) return;
    const src = map.getSource(TRAIL_LINE_SOURCE);
    if (!src) return;

    if (trailId == null) {
      src.setData({ type: 'FeatureCollection', features: [] });
      return;
    }

    try {
      const res = await fetch(`/api/v1/trails/${trailId}/geometry`);
      if (!res.ok) {
        src.setData({ type: 'FeatureCollection', features: [] });
        return;
      }
      const geojson = await res.json();
      src.setData(geojson);
      // Fit bounds if geometry has coordinates
      if (geojson.bbox) {
        map.fitBounds(geojson.bbox, { padding: 60 });
      }
    } catch (_) {
      src.setData({ type: 'FeatureCollection', features: [] });
    }
  }

  onMount(() => {
    initMap();
  });

  onDestroy(() => {
    if (map) {
      const m = map;
      map = null; // nullify reference before teardown to prevent post-destroy callbacks
      m.remove();
    }
  });
</script>

<div bind:this={mapContainer} class="map-container"></div>

<style>
  .map-container {
    width: 100%;
    height: 100%;
    display: block;
  }
</style>
