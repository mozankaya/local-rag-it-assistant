const percentageFormatter = new Intl.NumberFormat("tr-TR", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 1,
});

export function formatPercentage(value: number) {
  return `%${percentageFormatter.format(value)}`;
}
