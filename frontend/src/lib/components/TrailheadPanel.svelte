<script lang="ts">
  import { onMount } from 'svelte';
  import type { Trail, Trailhead } from '$lib/types';
  import TrailCard from './TrailCard.svelte';

  export let trailheadId: number | null = null;
  export let onTrailSelect: (trailId: number) => void = () => {};
  export let onClose: () => void = () => {};

  let trailhead: Trailhead | null = null;
  let trails: Trail[] = [];
  let loading = false;
  let error: string | null = null;

  const DIFFICULTY_ORDER: Record<string, number> = { T: 0, E: 1, EE: 2, EEA: 3 };

  function sortedTrails(list: Trail[]): Trail[] {
    return [...list].sort((a, b) => {
      const da = DIFFICULTY_ORDER[a.difficulty] ?? 99;
      const db = DIFFICULTY_ORDER[b.difficulty] ?? 99;
      if (da !== db) return da - db;
      return (a.length_km ?? 0) - (b.length_km ?? 0);
    });
  }

  async function loadTrailhead(id: number) {
    loading = true;
    error = null;
    trailhead = null;
    trails = [];
    try {
      const [thRes, trRes] = await Promise.all([
        fetch(`/api/v1/trailheads/${id}`),
        fetch(`/api/v1/trailheads/${id}/trails`),
      ]);
      if (!thRes.ok) throw new Error('Trailhead not found');
      if (!trRes.ok) throw new Error('Trails not found');
      [trailhead, trails] = await Promise.all([thRes.json(), trRes.json()]);
    } catch (e: any) {
      error = e?.message ?? 'Errore nel caricamento';
    } finally {
      loading = false;
    }
  }

  $: if (trailheadId != null) {
    loadTrailhead(trailheadId);
  } else {
    trailhead = null;
    trails = [];
    loading = false;
    error = null;
  }

  $: sorted = sortedTrails(trails);
</script>

{#if trailheadId != null}
  <aside class="panel" class:visible={trailheadId != null}>
    <header class="panel-header">
      <div class="panel-title">
        {#if loading}
          <span class="panel-name placeholder">Caricamento…</span>
        {:else if trailhead}
          <span class="panel-name">{trailhead.name}</span>
          <span class="trail-count">{trails.length} {trails.length === 1 ? 'sentiero' : 'sentieri'}</span>
        {:else if error}
          <span class="panel-name error">{error}</span>
        {/if}
      </div>
      <button class="close-btn" on:click={onClose} aria-label="Chiudi pannello">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </header>

    <div class="panel-body">
      {#if loading}
        <div class="spinner-wrap">
          <span class="spinner" aria-label="Caricamento"></span>
        </div>
      {:else if error}
        <p class="error-msg">{error}</p>
      {:else if sorted.length === 0}
        <p class="empty-msg">Nessun sentiero disponibile per questo trailhead.</p>
      {:else}
        <ul class="trail-list">
          {#each sorted as trail (trail.id)}
            <li>
              <TrailCard {trail} onClick={() => onTrailSelect(trail.id)} />
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </aside>
{/if}

<style>
  .panel {
    position: fixed;
    top: 0;
    right: 0;
    width: 380px;
    height: 100%;
    background: var(--color-surface, #fff);
    box-shadow: var(--shadow-lg, -4px 0 24px rgba(0,0,0,0.12));
    display: flex;
    flex-direction: column;
    z-index: 200;
    transform: translateX(100%);
    transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
  }

  .panel.visible {
    transform: translateX(0);
  }

  .panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 20px 20px 16px;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    flex-shrink: 0;
  }

  .panel-title {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .panel-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--color-text, #212529);
    line-height: 1.3;
    word-break: break-word;
  }

  .panel-name.placeholder {
    color: #aaa;
    font-weight: 400;
  }

  .panel-name.error {
    color: var(--color-danger, #e63946);
    font-size: 0.95rem;
    font-weight: 500;
  }

  .trail-count {
    font-size: 0.82rem;
    color: #6c757d;
    font-weight: 500;
  }

  .close-btn {
    flex-shrink: 0;
    background: none;
    border: none;
    cursor: pointer;
    color: #6c757d;
    padding: 4px;
    border-radius: var(--radius-sm, 4px);
    display: flex;
    align-items: center;
    transition: background 0.15s;
  }

  .close-btn:hover {
    background: rgba(0,0,0,0.06);
    color: var(--color-text, #212529);
  }

  .panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px 12px 24px;
  }

  .spinner-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 48px 0;
  }

  .spinner {
    display: inline-block;
    width: 36px;
    height: 36px;
    border: 3px solid rgba(45,106,79,0.2);
    border-top-color: var(--color-primary, #2d6a4f);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .error-msg,
  .empty-msg {
    color: #6c757d;
    font-size: 0.9rem;
    text-align: center;
    padding: 32px 16px;
    line-height: 1.5;
  }

  .error-msg {
    color: var(--color-danger, #e63946);
  }

  .trail-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  /* Mobile: bottom sheet */
  @media (max-width: 767px) {
    .panel {
      top: auto;
      bottom: 0;
      right: 0;
      left: 0;
      width: 100%;
      height: 60vh;
      border-radius: 16px 16px 0 0;
      transform: translateY(100%);
      transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .panel.visible {
      transform: translateY(0);
    }
  }
</style>
