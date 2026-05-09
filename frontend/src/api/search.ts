import { API_BASE_URL } from '../config';
import { Guest, AnalyzeQueryResponse } from '../types';

export interface SearchStartResponse {
  search_id: string;
}

export async function analyzeQuery(query: string): Promise<AnalyzeQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analyze-query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);
  return res.json();
}

export interface SearchEventStatus {
  type: 'status';
  message: string;
  step?: string;
}

export interface SearchEventLead {
  type: 'lead';
  data: Guest;
}

export interface SearchEventDone {
  type: 'done';
  total_leads: number;
}

export interface SearchEventError {
  type: 'error';
  message: string;
}

export type SearchEvent = SearchEventStatus | SearchEventLead | SearchEventDone | SearchEventError;

export interface SearchParams {
  query: string;
  seed_handles?: string[];
  podcast_description?: string;
  clarification_answers?: Record<string, string>;
}

export async function startSearch(params: SearchParams): Promise<SearchStartResponse> {
  const res = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}

export function getStreamUrl(searchId: string): string {
  return `${API_BASE_URL}/api/search/${searchId}/stream`;
}

export function getExportUrl(searchId: string): string {
  return `${API_BASE_URL}/api/search/${searchId}/export`;
}

export async function detectFilters(query: string): Promise<Record<string, string | null>> {
  const res = await fetch(`${API_BASE_URL}/api/detect-filters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('detect-filters failed');
  const data = await res.json();
  return data.filters;
}
