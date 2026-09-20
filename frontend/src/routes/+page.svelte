<script lang="ts">
  import { browser } from '$app/environment';
  import MapView from '$lib/components/MapView.svelte';
  import TrailheadPanel from '$lib/components/TrailheadPanel.svelte';

  export const ssr = false;

  let selectedTrailheadId: number | null = null;
  let selectedTrailId: number | null = null;

  function handleTrailheadClick(event: CustomEvent<{ id: number }>) {
    selectedTrailheadId = event.detail.id;
    selectedTrailId = null;
  }

  function handleTrailSelect(event: CustomEvent<{ id: number }>) {
    selectedTrailId = event.detail.id;
  }

  function closePanel() {
    selectedTrailheadId = null;
    selectedTrailId = null;
  }
</script>

<svelte:head>
  <title>Trail Explorer — Sentieri CAI Nord Italia</title>
</svelte:head>

<div class="map-root">
  {#if browser}
    <MapView
      {selectedTrailId}
      on:trailheadClick={handleTrailheadClick}
      on:trailSelect={handleTrailSelect}
    />
  {/if}

  {#if selectedTrailheadId !== null}
    <div class="panel-wrapper">
      <button class="close-btn" on:click={closePanel} aria-label="Chiudi pannello">✕</button>
      <TrailheadPanel
        trailheadId={selectedTrailheadId}
        {selectedTrailId}
        on:trailSelect={handleTrailSelect}
      />
    </div>
  {/if}
</div>

<style>
  .map-root {
    position: relative;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  .panel-wrapper {
    position: absolute;
    top: 0;
    right: 0;
    height: 100%;
    width: 360px;
    max-width: 100vw;
    z-index: 10;
    display: flex;
    flex-direction: column;
  }

  .close-btn {
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
    z-index: 20;
    background: var(--color-surface);
    border: none;
    border-radius: var(--radius-sm);
    width: 2rem;
    height: 2rem;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-sm);
    color: var(--color-text);
  }

  .close-btn:hover {
    background: var(--color-bg);
  }
</style>
