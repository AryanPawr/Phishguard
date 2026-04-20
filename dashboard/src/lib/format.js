export function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

export function shortHash(value) {
  if (!value) return "unknown";
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

export function dateTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

