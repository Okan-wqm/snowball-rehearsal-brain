import { test } from "node:test";
import assert from "node:assert/strict";
import { canEdit } from "../src/permissions.js";

test("admins and editors can edit", () => {
  assert.equal(canEdit({ level: "admin" }), true);
  assert.equal(canEdit({ level: "user", editor: true }), true);
});

test("others cannot", () => {
  assert.equal(canEdit({ level: "user" }), false);
  assert.equal(canEdit({ level: "user", editor: "yes" }), false);
});
