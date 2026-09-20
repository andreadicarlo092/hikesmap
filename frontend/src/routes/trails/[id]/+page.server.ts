import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import type { TrailFeature, ElevationProfile } from '$lib/types';

const API_URL = process.env.API_URL ?? 'http://localhost:8000';

async function fetchTrail(id: string, fetch: typeof globalThis.fetch): Promise<TrailFeature> {
	const res = await fetch(`${API_URL}/api/v1/trails/${id}`);
	if (res.status === 404) {
		throw error(404, 'Sentiero non trovato');
	}
	if (!res.ok) {
		throw error(res.status, `Errore nel recupero del sentiero: ${res.statusText}`);
	}
	return res.json();
}

async function fetchElevationProfile(id: string, fetch: typeof globalThis.fetch): Promise<ElevationProfile> {
	const res = await fetch(`${API_URL}/api/v1/trails/${id}/elevation`);
	if (res.status === 404) {
		throw error(404, 'Sentiero non trovato');
	}
	if (!res.ok) {
		throw error(res.status, `Errore nel recupero del profilo altimetrico: ${res.statusText}`);
	}
	return res.json();
}

export const load: PageServerLoad = async ({ params, fetch }) => {
	const { id } = params;

	const [trail, elevationProfile] = await Promise.all([
		fetchTrail(id, fetch),
		fetchElevationProfile(id, fetch)
	]);

	return { trail, elevationProfile };
};
