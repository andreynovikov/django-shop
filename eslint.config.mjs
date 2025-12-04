import nextCoreWebVitals from "eslint-config-next/core-web-vitals"
import nextTypescript from "eslint-config-next/typescript"

const eslintConfig = [
  ...nextCoreWebVitals,
  ...nextTypescript,
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