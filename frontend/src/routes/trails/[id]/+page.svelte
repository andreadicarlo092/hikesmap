<script lang="ts">
	import type { PageData } from './$types';
	import TrailMap from '$lib/components/TrailMap.svelte';
	import ElevationChart from '$lib/components/ElevationChart.svelte';

	export let data: PageData;

	$: trail = data.trail;
	$: elevationProfile = data.elevationProfile;
	$: props = trail.properties;

	function formatDuration(lengthKm: number, gainM: number): string {
		const hours = lengthKm / 4 + gainM / 400;
		const rounded = Math.round(hours * 2) / 2;
		if (rounded < 0.5) return '< 30 min';
		const h = Math.floor(rounded);
		const half = rounded % 1 !== 0;
		if (h === 0) return '30 min';
		return half ? `${h}h 30min` : `${h}h`;
	}

	function formatLength(km: number): string {
		return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
	}

	$: difficultyLabel = {
		T: 'Turistico',
		E: 'Escursionistico',
		EE: 'Escursionistico Esperto',
		EEA: 'Alpinistico'
	}[props.difficulty ?? 'E'] ?? props.difficulty;
</script>

<svelte:head>
	<title>{props.name ?? 'Sentiero'} — Trail Explorer</title>
	<meta
		name="description"
		content="Sentiero {difficultyLabel}, {props.length_km ? formatLength(props.length_km) : ''}. Esplora il tracciato, il profilo altimetrico e tutti i dettagli su Trail Explorer."
	/>
	<meta property="og:title" content="{props.name ?? 'Sentiero'} — Trail Explorer" />
	<meta
		property="og:description"
		content="Sentiero {difficultyLabel}, {props.length_km ? formatLength(props.length_km) : ''}. Esplora il tracciato, il profilo altimetrico e tutti i dettagli su Trail Explorer."
	/>
</svelte:head>

<div class="trail-detail">
	<nav class="breadcrumb">
		<a href="/" class="back-link">← Torna alla mappa</a>
	</nav>

	<div class="trail-layout">
		<!-- Colonna sinistra: mappa + grafico -->
		<div class="trail-left">
			<div class="trail-map-container">
				<TrailMap {trail} />
			</div>
			{#if elevationProfile != null}
				<div class="elevation-container">
					<ElevationChart profile={elevationProfile} />
				</div>
			{/if}
		</div>

		<!-- Colonna destra: dettagli -->
		<div class="trail-right">
			<span class="difficulty-badge difficulty-{props.difficulty}">{difficultyLabel}</span>

			<h1 class="trail-title">{props.name ?? 'Sentiero senza nome'}</h1>

			{#if props.cai_ref}
				<p class="cai-ref">Sentiero CAI {props.cai_ref}</p>
			{/if}

			<div class="trail-stats">
				<div class="stat-item">
					<span class="stat-label">Lunghezza</span>
					<span class="stat-value">{props.length_km ? formatLength(props.length_km) : '—'}</span>
				</div>
				<div class="stat-item">
					<span class="stat-label">Dislivello ↑</span>
					<span class="stat-value">{props.elevation_gain_m != null ? `${props.elevation_gain_m} m` : '—'}</span>
				</div>
				<div class="stat-item">
					<span class="stat-label">Dislivello ↓</span>
					<span class="stat-value">{props.elevation_loss_m != null ? `${props.elevation_loss_m} m` : '—'}</span>
				</div>
				<div class="stat-item">
					<span class="stat-label">Durata stimata</span>
					<span class="stat-value">
						{#if props.duration_hours != null}
							{formatDuration(props.duration_hours, 0)}
						{:else if props.length_km != null && props.elevation_gain_m != null}
							{formatDuration(props.length_km, props.elevation_gain_m)}
						{:else}
							—
						{/if}
					</span>
				</div>
				<div class="stat-item">
					<span class="stat-label">Quota min</span>
					<span class="stat-value">
						{#if elevationProfile != null && elevationProfile.min_alt_m != null}
							{elevationProfile.min_alt_m} m
						{:else}
							—
						{/if}
					</span>
				</div>
				<div class="stat-item">
					<span class="stat-label">Quota max</span>
					<span class="stat-value">
						{#if elevationProfile != null && elevationProfile.max_alt_m != null}
							{elevationProfile.max_alt_m} m
						{:else}
							—
						{/if}
					</span>
				</div>
			</div>

			<div class="trail-actions">
				<a
					href="/api/v1/trails/{trail.properties.id}/gpx"
					class="btn btn-primary"
					download
				>
					Esporta GPX
				</a>
				{#if props.osm_url}
					<a
						href={props.osm_url}
						class="btn btn-secondary"
						target="_blank"
						rel="noopener noreferrer"
					>
						Apri in OpenStreetMap
					</a>
				{/if}
			</div>

			<p class="osm-note">
				Dati OSM — licenza ODbL. Contribuisci su <a href="https://www.openstreetmap.org" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>.
			</p>
		</div>
	</div>
</div>

<style>
	.trail-detail {
		min-height: 100vh;
		background: var(--color-background);
		padding: var(--space-4);
	}

	.breadcrumb {
		margin-bottom: var(--space-4);
	}

	.back-link {
		color: var(--color-primary);
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 500;
	}

	.back-link:hover {
		text-decoration: underline;
	}

	.trail-layout {
		display: grid;
		grid-template-columns: 60% 40%;
		gap: var(--space-6);
		max-width: 1280px;
		margin: 0 auto;
	}

	.trail-left {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.trail-map-container {
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.elevation-container {
		border-radius: var(--radius-md);
		background: var(--color-surface);
		padding: var(--space-4);
	}

	.trail-right {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.difficulty-badge {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		align-self: flex-start;
	}

	:global(.difficulty-T)   { background: #d1fae5; color: #065f46; }
	:global(.difficulty-E)   { background: #dbeafe; color: #1e3a8a; }
	:global(.difficulty-EE)  { background: #fef3c7; color: #92400e; }
	:global(.difficulty-EEA) { background: #fee2e2; color: #7f1d1d; }

	.trail-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--color-text);
		margin: 0;
		line-height: 1.2;
	}

	.cai-ref {
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		margin: 0;
	}

	.trail-stats {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-3);
		background: var(--color-surface);
		border-radius: var(--radius-md);
		padding: var(--space-4);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.stat-label {
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.stat-value {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.trail-actions {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.625rem 1.25rem;
		border-radius: var(--radius-sm);
		font-weight: 600;
		font-size: 0.9375rem;
		text-decoration: none;
		transition: opacity 0.15s;
	}

	.btn:hover {
		opacity: 0.85;
	}

	.btn-primary {
		background: var(--color-primary);
		color: #fff;
	}

	.btn-secondary {
		background: var(--color-surface);
		color: var(--color-primary);
		border: 1px solid var(--color-primary);
	}

	.osm-note {
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		margin: 0;
	}

	.osm-note a {
		color: var(--color-primary);
		text-decoration: underline;
	}

	@media (max-width: 767px) {
		.trail-layout {
			grid-template-columns: 1fr;
		}

		.trail-title {
			font-size: 1.375rem;
		}
	}
</style>
