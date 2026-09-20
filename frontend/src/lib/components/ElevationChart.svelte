<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { ElevationProfile } from '$lib/types';

  export let profile: ElevationProfile;

  let canvas: HTMLCanvasElement;
  let chart: import('chart.js').Chart | null = null;

  onMount(async () => {
    if (typeof window === 'undefined') return;
    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);

    const labels = profile.samples.map((s) => s.d_km);
    const data   = profile.samples.map((s) => s.alt_m);

    chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Quota (m)',
            data,
            fill: true,
            borderColor: 'var(--color-primary)',
            backgroundColor: 'rgba(45,106,79,0.15)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const d = profile.samples[ctx.dataIndex];
                return `${d.d_km} km — ${d.alt_m} m`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: 'km' },
            ticks: { maxTicksLimit: 8 },
          },
          y: {
            title: { display: true, text: 'm slm' },
          },
        },
      },
    });
  });

  onDestroy(() => {
    chart?.destroy();
    chart = null;
  });
</script>

<div class="elevation-chart">
  <div class="canvas-wrapper">
    <canvas bind:this={canvas}></canvas>
  </div>
  <div class="stats">
    <span class="stat"><span class="arrow up">↑</span> {profile.gain_m} m</span>
    <span class="stat"><span class="arrow down">↓</span> {profile.loss_m} m</span>
    <span class="stat">max {profile.max_alt_m} m</span>
    <span class="stat">min {profile.min_alt_m} m</span>
  </div>
</div>

<style>
  .elevation-chart {
    width: 100%;
  }

  .canvas-wrapper {
    width: 100%;
    height: 200px;
    position: relative;
  }

  canvas {
    width: 100% !important;
    height: 100% !important;
  }

  .stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: var(--color-text);
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 0.2rem;
  }

  .arrow.up   { color: var(--color-primary); font-weight: 700; }
  .arrow.down { color: var(--color-danger);  font-weight: 700; }
</style>
