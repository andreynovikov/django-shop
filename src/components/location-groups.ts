import { City, Country } from '@/lib/types'

export type CityGroup<T> = {
  city: City
  items: T[]
}

export type CountryGroup<T> = {
  country: Country
  cities: CityGroup<T>[]
}

// Groups stores or service centers by country and city, the backend returns them ordered by both
export function groupByCountryAndCity<T extends { city: City }>(items: T[]) {
  return items.reduce((groups, item) => {
    let countryGroup = groups.at(-1)
    if (countryGroup?.country.id !== item.city.country.id) {
      countryGroup = { country: item.city.country, cities: [] }
      groups.push(countryGroup)
    }
    let cityGroup = countryGroup.cities.at(-1)
    if (cityGroup?.city.id !== item.city.id) {
      cityGroup = { city: item.city, items: [] }
      countryGroup.cities.push(cityGroup)
    }
    cityGroup.items.push(item)
    return groups
  }, [] as CountryGroup<T>[])
}
