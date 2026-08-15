export interface Player {
  id: string
  name: string
  username: string | null
  color: string | null
  isYou: boolean
  isRandom: boolean
  favorite: boolean
  mergedIntoId: string | null
}

export interface Commander {
  id: string
  name: string
  colors: string[] | null
  imageUri: string | null
  edhrecRank: number | null
  cmc: number | null
  deckName: string | null
  decklistUrl: string | null
  edhrecUrl: string
}

export interface OwnedDeckCard {
  cardName: string
  setCode: string | null
  collectorNumber: string | null
  quantity: number
  isFoil: boolean
  isCommander: boolean
}

export interface OwnedDeck {
  id: string
  ownerId: string
  ownerName: string
  commanderId: string
  commanderName: string
  name: string | null
  source: string
  moxfieldDeckId: string | null
  moxfieldUrl: string | null
  edhrecUrl: string
  cardCount: number
}

export interface OwnedDeckDetail extends OwnedDeck {
  cards: OwnedDeckCard[]
}

export interface BinderCard {
  cardName: string
  setCode: string | null
  collectorNumber: string | null
  quantity: number
  isFoil: boolean
}

export type RecommendationAction = 'add' | 'remove'
export type RecommendationStatus = 'proposed' | 'approved' | 'ignored'
export type ArchetypeRole = 'ramp' | 'draw' | 'removal' | 'land'

export interface Recommendation {
  id: string
  deckId: string
  action: RecommendationAction
  cardName: string
  inclusionRate: number
  role: ArchetypeRole | null
  status: RecommendationStatus
  appliedAt: string | null
  createdAt: string
}

export interface ArchetypeRoleStat {
  count: number
  target: number
  met: boolean
}

export type ArchetypeStats = Record<ArchetypeRole, ArchetypeRoleStat>

export interface CardSyncStatus {
  cardCount: number
  syncedAt: string | null
}

export interface DeckStat {
  commanderId: string
  commanderName: string
  gamesPlayed: number
  wins: number
  winRate: number
  lastPlayed: string | null
  firstPlayed: string | null
  daysSinceLastPlayed: number | null
  retired: boolean
}

export interface SpeedDeckStat extends DeckStat {
  avg: number
  min: number
  max: number
  unit: 'minutes' | 'turns'
}

export interface Streak {
  length: number
  startDate: string | null
  endDate: string | null
}

export interface PlayerStreaks {
  longestWinStreak: Streak
  longestLossStreak: Streak
}

export interface PlayerSummary {
  decks: DeckStat[]
  leastPlayed: DeckStat[]
  longestSincePlayed: DeckStat[]
  fastestToWin: SpeedDeckStat[]
  slowestToWin: SpeedDeckStat[]
  streaks: PlayerStreaks
}

export interface YearlyPlayerByUniqueDecks {
  playerId: string
  name: string
  uniqueDecks: number
  games: number
}

export interface YearlyPlayerByWinRate {
  playerId: string
  name: string
  games: number
  wins: number
  rate: number
}

export interface YearlyPlayerByWins {
  playerId: string
  name: string
  wins: number
  games: number
}

export interface YearlyPlayerByGames {
  playerId: string
  name: string
  games: number
  uniqueDecks: number
}

export interface YearlyPlayerStreak {
  playerId: string
  name: string
  length: number
  startDate: string | null
  endDate: string | null
}

export interface YearlyCommanderByMostPlayed {
  commanderId: string
  name: string
  games: number
  players: number
  wins: number
}

export interface YearlyCommanderByMostWins {
  commanderId: string
  name: string
  wins: number
  games: number
  rate: number
}

export interface YearlyCommanderSpeed {
  commanderId: string
  name: string
  wins: number
  avg: number
  min: number
  max: number
}

export interface YearlySummary {
  year: number
  totalGames: number
  avgMinutesPerGame: number | null
  avgTurnsPerGame: number | null
  uniquePlayers: number
  uniqueCommanders: number
  playersByUniqueDecks: YearlyPlayerByUniqueDecks[]
  playersByWinRate: YearlyPlayerByWinRate[]
  playersByWins: YearlyPlayerByWins[]
  playersByGames: YearlyPlayerByGames[]
  playersByWinStreak: YearlyPlayerStreak[]
  playersByLossStreak: YearlyPlayerStreak[]
  commandersByMostPlayed: YearlyCommanderByMostPlayed[]
  commandersByMostWins: YearlyCommanderByMostWins[]
  commandersFastestToWin: YearlyCommanderSpeed[]
  commandersSlowestToWin: YearlyCommanderSpeed[]
}
