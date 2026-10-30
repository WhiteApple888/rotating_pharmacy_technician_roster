// Grid cells are text, but the optimizer expects numeric priority cells.
export function gridPriorityValue(value: string, rowIndex: number, columnIndex: number) {
  if (rowIndex < 5 || rowIndex >= 21 || ![2, 13, 24, 35].includes(columnIndex)) {
    return value
  }

  const trimmed = value.trim()
  if (!/^[+-]?\d+(?:\.\d+)?$/.test(trimmed)) return value
  const number = Number(trimmed)
  return Number.isFinite(number) ? number : value
}
