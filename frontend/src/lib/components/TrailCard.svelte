<script lang="ts">
  import type { Trail } from '$lib/types';

  export let trail: Trail;
  export let onClick: () => void = () => {};

  // CAI estimated duration: dist(km)/4 + gain(m)/400, rounded to nearest 0.5h
  function estimateDuration(distKm: number | null | undefined, gainM: number | null | undefined): string {
    const d = distKm ?? 0;
    const g = gainM ?? 0;
    const raw = d / 4 + g / 400;
    const rounded = Math.round(raw * 2) / 2;
    if (rounded < 0.5) return '< 30 min';
    if (rounded < 1) return '30 min';
    const h = Math.floor(rounded);
    const mins = (rounded - h) === 0.5 ? 30 : 0;
    if (mins === 0) return `${h}h`;
    return `${h}h 30min`;
  }

  const difficultyLabels: Record<string, string> = {
    T: 'T',
    E: 'E',
    EE: 'EE',
    EEA: 'EEA',
  };

  $: duration = estimateDuration(trail.length_km, trail.elevation_gain_m);
</script>

<button class="trail-card" on:click={onClick} type="button">
  <div class="card-top">
    <span class="difficulty-badge difficulty-{trail.difficulty}" aria-label="Difficoltà {trail.difficulty}">
      {difficultyLabels[trail.difficulty] ?? trail.difficulty}
    </span>
    <div class="card-name-wrap">
      <span class="trail-name">{trail.name}</span>
      {#if trail.cai_ref}
        <span class="cai-ref">{trail.cai_ref}</span>
      {/if}
    </div>
  </div>

  <div class="card-stats">
    {#if trail.length_km != null}
      <span class="stat">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13" aria-hidden="true">
          <path d="M2 8h12M10 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {trail.length_km.toFixed(1)} km
      </span>
    {/if}
    {#if trail.elevation_gain_m != null}
      <span class="stat">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13" aria-hidden="true">
          <path d="M8 13V3M4 7l4-4 4 4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        +{trail.elevation_gain_m} m
      </span>
    {/if}
    <span class="stat">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13" aria-hidden="true">
        <circle cx="8" cy="8" r="6"/><path d="M8 5v3.5l2 1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {duration}
    </span>
  </div>

  {#if trail.tags && trail.tags.length > 0}
    <div class="card-tags">
      {#each trail.tags as tag (tag)}
        <span class="tag">{tag}</span>
      {/each}
    </div>
  {/if}
</button>

<style>
  .trail-card {
    width: 100%;
    background: var(--color-bg, #f8f9fa);
    border: 1px solid rgba(0,0,0,0.07);
    border-radius: var(--radius-md, 8px);
    padding: 12px 14px;
    text-align: left;
    cursor: pointer;
    transition: background 0.15s, box-shadow 0.15s;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-family: inherit;
    font-size: 0.9rem;
    color: var(--color-text, #212529);
  }

  .trail-card:hover,
  .trail-card:focus-visible {
    background: #eef0f2;
    box-shadow: var(--shadow-sm, 0 1px 4px rgba(0,0,0,0.08));
    outline: none;
  }

  .trail-card:focus-visible {
    outline: 2px solid var(--color-primary, #2d6a4f);
    outline-offset: 2px;
  }

  .card-top {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .difficulty-badge {
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 2px 7px;
    border-radius: var(--radius-sm, 4px);
    text-transform: uppercase;
  }

  /* Reuse classes from app.css */
  :global(.difficulty-T)   { background: #d8f3dc; color: #1b4332; }
  :global(.difficulty-E)   { background: #b7e4c7; color: #1b4332; }
  :global(.difficulty-EE)  { background: #fde68a; color: #78350f; }
  :global(.difficulty-EEA) { background: #fecaca; color: #7f1d1d; }

  .card-name-wrap {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .trail-name {
    font-weight: 600;
    font-size: 0.92rem;
    line-height: 1.35;
    word-break: break-word;
  }

  .cai-ref {
    font-size: 0.75rem;
    color: #6c757d;
    font-family: 'Fira Code', monospace;
  }

  .card-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8rem;
    color: #495057;
    white-space: nowrap;
  }

  .stat svg {
    flex-shrink: 0;
    opacity: 0.7;
  }

  .card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .tag {
    font-size: 0.72rem;
    padding: 1px 7px;
    border-radius: 100px;
    background: rgba(45,106,79,0.1);
    color: var(--color-primary, #2d6a4f);
    font-weight: 500;
  }
</style>
