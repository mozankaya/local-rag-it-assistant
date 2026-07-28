export function humanize(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/^./, (letter) => letter.toLocaleUpperCase("tr-TR"));
}
