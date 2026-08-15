import type {
  ArchetypeStats,
  BinderCard,
  CardSyncStatus,
  Commander,
  OwnedDeck,
  OwnedDeckDetail,
  Player,
  PlayerSummary,
  Recommendation,
  RecommendationStatus,
  YearlySummary,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.error ?? `Request failed: ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function listPlayers(): Promise<Player[]> {
  return request<Player[]>('/players')
}

export function getPlayer(id: string): Promise<Player> {
  return request<Player>(`/players/${id}`)
}

export function getPlayerSummary(id: string): Promise<PlayerSummary> {
  return request<PlayerSummary>(`/players/${id}/summary?limit=10`)
}

export function listCommanders(search?: string): Promise<Commander[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : ''
  return request<Commander[]>(`/commanders${qs}`)
}

export function getCommander(id: string): Promise<Commander> {
  return request<Commander>(`/commanders/${id}`)
}

export function getYearlyReport(year?: number): Promise<YearlySummary> {
  const qs = year ? `?year=${year}` : ''
  return request<YearlySummary>(`/reports/yearly${qs}`)
}

export function listPlayerDecks(playerId: string): Promise<OwnedDeck[]> {
  return request<OwnedDeck[]>(`/decks?playerId=${playerId}`)
}

export function getDeck(id: string): Promise<OwnedDeckDetail> {
  return request<OwnedDeckDetail>(`/decks/${id}`)
}

interface CreateDeckPayload {
  ownerId: string
  commanderId: string
  exportText: string
  name?: string
  moxfieldUrl?: string
}

export function createDeck(payload: CreateDeckPayload): Promise<OwnedDeckDetail> {
  return request<OwnedDeckDetail>('/decks', { method: 'POST', body: JSON.stringify(payload) })
}

export function replaceDeckCards(id: string, exportText: string): Promise<OwnedDeckDetail> {
  return request<OwnedDeckDetail>(`/decks/${id}/cards`, {
    method: 'PUT',
    body: JSON.stringify({ exportText }),
  })
}

export function deleteDeck(id: string): Promise<void> {
  return request<void>(`/decks/${id}`, { method: 'DELETE' })
}

export function getBinder(playerId: string): Promise<BinderCard[]> {
  return request<BinderCard[]>(`/players/${playerId}/binder`)
}

export function replaceBinder(playerId: string, exportText: string): Promise<BinderCard[]> {
  return request<BinderCard[]>(`/players/${playerId}/binder`, {
    method: 'PUT',
    body: JSON.stringify({ exportText }),
  })
}

export function getRecommendations(deckId: string): Promise<Recommendation[]> {
  return request<Recommendation[]>(`/decks/${deckId}/recommendations`)
}

export function generateRecommendations(deckId: string): Promise<Recommendation[]> {
  return request<Recommendation[]>(`/decks/${deckId}/recommendations/generate`, { method: 'POST' })
}

export function updateRecommendation(
  id: string,
  update: { status?: RecommendationStatus; applied?: boolean },
): Promise<Recommendation> {
  return request<Recommendation>(`/recommendations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export function getArchetypeStats(deckId: string): Promise<ArchetypeStats> {
  return request<ArchetypeStats>(`/decks/${deckId}/archetype-stats`)
}

export function getCardSyncStatus(): Promise<CardSyncStatus> {
  return request<CardSyncStatus>('/cards/sync-status')
}

export function syncCards(): Promise<CardSyncStatus> {
  return request<CardSyncStatus>('/cards/sync', { method: 'POST' })
}
