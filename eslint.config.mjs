import nextCoreWebVitals from "eslint-config-next/core-web-vitals"
import nextTypescript from "eslint-config-next/typescript"
import tanstackQuery from "@tanstack/eslint-plugin-query"

const eslintConfig = [
  ...nextCoreWebVitals,
  ...nextTypescript,
  ...tanstackQuery.configs["flat/recommended"],
  {
    rules: {
      "react-hooks/exhaustive-deps": "warn",
    },
  },
  {
    ignores: [
      "**/vendor/*",
    ]
  }
]

export default eslintConfig