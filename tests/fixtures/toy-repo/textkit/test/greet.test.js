import { test } from "node:test";
import assert from "node:assert/strict";
import { greet, title } from "../src/greet.js";

test("greet", () => {
  assert.equal(greet("Ada"), "Hello, Ada!");
});

test("title trims the title field", () => {
  assert.equal(title({ title: "  Notes " }), "Notes");
});
