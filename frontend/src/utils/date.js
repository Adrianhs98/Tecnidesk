const dateFormatter = new Intl.DateTimeFormat("es-EC", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const onlyDateFormatter = new Intl.DateTimeFormat("es-EC", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatDate(iso) {
  if (!iso) return "-";
  return dateFormatter.format(new Date(iso));
}

export function formatOnlyDate(iso) {
  if (!iso) return "-";
  return onlyDateFormatter.format(new Date(iso));
}
