export default [
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: "module",
    },
    rules: {
      "dot-notation": "error",
      "no-var": "error",
      "object-shorthand": "error",
      "operator-assignment": "error",
      "prefer-const": "error",
      "prefer-template": "error",
      "yoda": "error",
    },
  },
];
