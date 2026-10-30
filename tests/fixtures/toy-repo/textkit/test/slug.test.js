import { test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "../src/slug.js";

test("slugify lowers, joins words with dashes and trims dashes", () => {
  assert.equal(slugify("  Hello, World!  "), "hello-world");
  assert.equal(slugify("a--b"), "a-b");
  assert.equal(slugify(""), "");
});
