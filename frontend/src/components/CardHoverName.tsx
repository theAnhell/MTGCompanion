import { useState } from 'react'
import type { MouseEvent } from 'react'

const PREVIEW_WIDTH = 224
const PREVIEW_HEIGHT = 312
const CURSOR_OFFSET = 16

function scryfallImageUrl(scryfallId: string): string {
  return `https://cards.scryfall.io/normal/front/${scryfallId[0]}/${scryfallId[1]}/${scryfallId}.jpg`
}

export function CardHoverName({ name, scryfallId }: { name: string; scryfallId: string | null }) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)

  if (!scryfallId) return <>{name}</>

  function handleMove(e: MouseEvent) {
    const x = Math.min(e.clientX + CURSOR_OFFSET, window.innerWidth - PREVIEW_WIDTH - 8)
    const y = Math.min(e.clientY + CURSOR_OFFSET, window.innerHeight - PREVIEW_HEIGHT - 8)
    setPos({ x, y })
  }

  return (
    <span onMouseMove={handleMove} onMouseLeave={() => setPos(null)}>
      {name}
      {pos && (
        <img
          src={scryfallImageUrl(scryfallId)}
          alt={name}
          width={PREVIEW_WIDTH}
          style={{ left: pos.x, top: pos.y }}
          className="pointer-events-none fixed z-50 rounded-lg border border-border shadow-xl"
        />
      )}
    </span>
  )
}
