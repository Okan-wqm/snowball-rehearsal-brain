export function slugify(text) {
  let lower = text.toLowerCase();
  return lower.trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
