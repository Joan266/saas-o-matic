const AVATAR_COLORS = [
  '#c84b31', '#2e4057', '#1b6ca8', '#4a235a', '#1e5631',
  '#7d3c98', '#1a5276', '#784212', '#1b4f72', '#17202a',
];

export function avatarColor(company: string): string {
  const idx = company.charCodeAt(0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[idx];
}

export function initials(company: string): string {
  return company
    .split(' ')
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase();
}
