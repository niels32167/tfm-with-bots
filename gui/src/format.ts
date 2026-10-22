/** A number with an explicit sign and a real minus sign: "+8", "0", "−30". */
export function signed(value: number): string {
  if (value > 0) return `+${value}`;
  if (value < 0) return `−${-value}`;
  return "0";
}

export function formatTemperature(celsius: number): string {
  return `${signed(celsius)} °C`;
}
