import { Category } from './types'

interface CategoryWithParent extends Category {
  parent: number | null
  path: string[]
}

export function flattenCategoryTree(parent: Category, parentPath: string[], categories: Category[]) {
  return categories.reduce((acc, category) => {
    const { children, ...categoryWithoutChildren } = category
    const categoryPath = [...parentPath, categoryWithoutChildren.slug]
    acc.push({
      ...categoryWithoutChildren,
      parent: parent.id,
      path: categoryPath,
    })
    if (children) {
      acc.push(...flattenCategoryTree(categoryWithoutChildren, categoryPath, children))
    }
    return acc
  }, [] as CategoryWithParent[])
}

export function getCategoryDescendants(category: Category) {
  const { children, ...categoryWithoutChildren } = category
  if (children)
    return flattenCategoryTree(categoryWithoutChildren, [category.slug], children)
  else
    return []
}