export function mean(values) {
  if (values.length === 0) {
    return 0;
  }
  var total = 0;
  for (const value of values) {
    total = total + value;
  }
  return total / values.length;
}

export function summary(values) {
  const count = values.length;
  return { count: count, mean: mean(values) };
}
