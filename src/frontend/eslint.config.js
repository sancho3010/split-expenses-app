export default [
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        document: "readonly",
        window: "readonly",
        fetch: "readonly",
        setTimeout: "readonly",
        console: "readonly",
        api: "writable",
      },
    },
    rules: {
      "no-redeclare": "error",
      "no-unused-vars": ["warn", { "varsIgnorePattern": "^api$" }],
      "no-undef": "error",
      "no-duplicate-case": "error",
      "no-empty": "warn",
      "no-unreachable": "error",
      "eqeqeq": "warn",
    },
  },
];
