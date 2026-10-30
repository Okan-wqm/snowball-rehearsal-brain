import { test } from "node:test";
import assert from "node:assert/strict";
import { mean, summary } from "../src/stats.js";

test("mean of no values is 0", () => {
  assert.equal(mean([]), 0);
});

test("mean of values", () => {
  assert.equal(mean([1, 2, 3, 4]), 2.5);
});

test("summary counts and averages", () => {
  assert.deepEqual(summary([2, 4]), { count: 2, mean: 3 });
});
