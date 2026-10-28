// Subset of the schema.org vocabulary for the types the site marks up, used to validate microdata in tests.
// Generated from https://schema.org/version/latest/schemaorg-current-https.jsonld (release 30.1):
// each type lists its ancestors and every non-superseded property of it and its ancestors with the property's
// rangeIncludes. Regenerate it the same way when a new type is marked up.

export interface SchemaType {
  ancestors: string[]
  properties: Record<string, string[]>
}

export const schemaTypes: Record<string, SchemaType> = {
  "Product": {
    ancestors: [
      "Thing"
    ],
    properties: {
      "additionalProperty": [
        "PropertyValue"
      ],
      "additionalType": [
        "Text",
        "URL"
      ],
      "aggregateRating": [
        "AggregateRating"
      ],
      "alternateName": [
        "Text"
      ],
      "asin": [
        "Text",
        "URL"
      ],
      "audience": [
        "Audience"
      ],
      "authorizedRepresentative": [
        "Organization",
        "Person"
      ],
      "award": [
        "Text"
      ],
      "brand": [
        "Brand",
        "Organization"
      ],
      "category": [
        "CategoryCode",
        "PhysicalActivityCategory",
        "Text",
        "Thing",
        "URL"
      ],
      "color": [
        "Text"
      ],
      "colorSwatch": [
        "ImageObject",
        "URL"
      ],
      "consumerNotice": [
        "Text",
        "TextObject",
        "URL",
        "WebContent"
      ],
      "countryOfAssembly": [
        "Text"
      ],
      "countryOfLastProcessing": [
        "Text"
      ],
      "countryOfOrigin": [
        "Country"
      ],
      "depth": [
        "Distance",
        "QuantitativeValue"
      ],
      "description": [
        "Text",
        "TextObject"
      ],
      "disambiguatingDescription": [
        "Text"
      ],
      "displayLocation": [
        "Place"
      ],
      "funding": [
        "Grant"
      ],
      "gtin": [
        "Text",
        "URL"
      ],
      "gtin12": [
        "Text"
      ],
      "gtin13": [
        "Text"
      ],
      "gtin14": [
        "Text"
      ],
      "gtin8": [
        "Text"
      ],
      "hasAdultConsideration": [
        "AdultOrientedEnumeration"
      ],
      "hasCertification": [
        "Certification"
      ],
      "hasDigitalProductPassport": [
        "DigitalProductPassport",
        "URL"
      ],
      "hasEnergyConsumptionDetails": [
        "EnergyConsumptionDetails"
      ],
      "hasGS1DigitalLink": [
        "URL"
      ],
      "hasMeasurement": [
        "QuantitativeValue"
      ],
      "hasMerchantReturnPolicy": [
        "MerchantReturnPolicy"
      ],
      "height": [
        "Distance",
        "QuantitativeValue"
      ],
      "identifier": [
        "PropertyValue",
        "Text",
        "URL"
      ],
      "image": [
        "ImageObject",
        "URL"
      ],
      "importer": [
        "Organization",
        "Person"
      ],
      "inProductGroupWithID": [
        "Text"
      ],
      "isAccessoryOrSparePartFor": [
        "Product"
      ],
      "isConsumableFor": [
        "Product"
      ],
      "isFamilyFriendly": [
        "Boolean"
      ],
      "isOftenBoughtWith": [
        "Product"
      ],
      "isRelatedTo": [
        "Product",
        "Service"
      ],
      "isSimilarTo": [
        "Product",
        "Service"
      ],
      "isVariantOf": [
        "ProductGroup",
        "ProductModel"
      ],
      "itemCondition": [
        "OfferItemCondition"
      ],
      "keywords": [
        "DefinedTerm",
        "Text",
        "URL"
      ],
      "logo": [
        "ImageObject",
        "URL"
      ],
      "mainEntityOfPage": [
        "CreativeWork",
        "URL"
      ],
      "manufacturer": [
        "Organization"
      ],
      "material": [
        "Product",
        "Text",
        "URL"
      ],
      "mobileUrl": [
        "Text"
      ],
      "model": [
        "ProductModel",
        "Text"
      ],
      "mpn": [
        "Text"
      ],
      "name": [
        "Text"
      ],
      "negativeNotes": [
        "ItemList",
        "ListItem",
        "Text",
        "WebContent"
      ],
      "nsn": [
        "Text"
      ],
      "offers": [
        "Demand",
        "Offer"
      ],
      "owner": [
        "Organization",
        "Person"
      ],
      "pattern": [
        "DefinedTerm",
        "Text"
      ],
      "positiveNotes": [
        "ItemList",
        "ListItem",
        "Text",
        "WebContent"
      ],
      "potentialAction": [
        "Action"
      ],
      "productID": [
        "Text"
      ],
      "productionDate": [
        "Date"
      ],
      "purchaseDate": [
        "Date"
      ],
      "recycledContentPercentage": [
        "Number"
      ],
      "releaseDate": [
        "Date"
      ],
      "review": [
        "Review"
      ],
      "sameAs": [
        "URL"
      ],
      "size": [
        "DefinedTerm",
        "QuantitativeValue",
        "SizeSpecification",
        "Text"
      ],
      "sku": [
        "Text"
      ],
      "slogan": [
        "Text"
      ],
      "specification": [
        "PropertyValue"
      ],
      "subjectOf": [
        "CreativeWork",
        "Event"
      ],
      "substanceOfConcern": [
        "ChemicalSubstance",
        "DefinedTerm",
        "Text",
        "URL"
      ],
      "url": [
        "URL"
      ],
      "weight": [
        "Mass",
        "QuantitativeValue"
      ],
      "width": [
        "Distance",
        "QuantitativeValue"
      ]
    }
  },
  "Offer": {
    ancestors: [
      "Intangible",
      "Thing"
    ],
    properties: {
      "acceptedPaymentMethod": [
        "LoanOrCredit",
        "PaymentMethod",
        "Text"
      ],
      "addOn": [
        "Offer"
      ],
      "additionalProperty": [
        "PropertyValue"
      ],
      "additionalType": [
        "Text",
        "URL"
      ],
      "advanceBookingRequirement": [
        "QuantitativeValue"
      ],
      "aggregateRating": [
        "AggregateRating"
      ],
      "alternateName": [
        "Text"
      ],
      "areaServed": [
        "AdministrativeArea",
        "GeoShape",
        "Place",
        "Text"
      ],
      "asin": [
        "Text",
        "URL"
      ],
      "availability": [
        "ItemAvailability"
      ],
      "availabilityEnds": [
        "Date",
        "DateTime",
        "Time"
      ],
      "availabilityStarts": [
        "Date",
        "DateTime",
        "Time"
      ],
      "availableAtOrFrom": [
        "Place"
      ],
      "availableDeliveryMethod": [
        "DeliveryMethod"
      ],
      "businessFunction": [
        "BusinessFunction"
      ],
      "category": [
        "CategoryCode",
        "PhysicalActivityCategory",
        "Text",
        "Thing",
        "URL"
      ],
      "checkoutPageURLTemplate": [
        "Text"
      ],
      "deliveryLeadTime": [
        "QuantitativeValue"
      ],
      "description": [
        "Text",
        "TextObject"
      ],
      "disambiguatingDescription": [
        "Text"
      ],
      "eligibleCustomerType": [
        "BusinessEntityType"
      ],
      "eligibleDuration": [
        "QuantitativeValue"
      ],
      "eligibleQuantity": [
        "QuantitativeValue"
      ],
      "eligibleRegion": [
        "GeoShape",
        "Place",
        "Text"
      ],
      "eligibleTransactionVolume": [
        "PriceSpecification"
      ],
      "gtin": [
        "Text",
        "URL"
      ],
      "gtin12": [
        "Text"
      ],
      "gtin13": [
        "Text"
      ],
      "gtin14": [
        "Text"
      ],
      "gtin8": [
        "Text"
      ],
      "hasAdultConsideration": [
        "AdultOrientedEnumeration"
      ],
      "hasDigitalProductPassport": [
        "DigitalProductPassport",
        "URL"
      ],
      "hasGS1DigitalLink": [
        "URL"
      ],
      "hasMeasurement": [
        "QuantitativeValue"
      ],
      "hasMerchantReturnPolicy": [
        "MerchantReturnPolicy"
      ],
      "identifier": [
        "PropertyValue",
        "Text",
        "URL"
      ],
      "image": [
        "ImageObject",
        "URL"
      ],
      "includesObject": [
        "TypeAndQuantityNode"
      ],
      "ineligibleRegion": [
        "GeoShape",
        "Place",
        "Text"
      ],
      "inventoryLevel": [
        "QuantitativeValue"
      ],
      "isFamilyFriendly": [
        "Boolean"
      ],
      "itemCondition": [
        "OfferItemCondition"
      ],
      "itemOffered": [
        "AggregateOffer",
        "CreativeWork",
        "Event",
        "MenuItem",
        "Product",
        "Service",
        "Trip"
      ],
      "itemPopularity": [
        "Number",
        "QuantitativeValue"
      ],
      "leaseLength": [
        "Duration",
        "QuantitativeValue"
      ],
      "mainEntityOfPage": [
        "CreativeWork",
        "URL"
      ],
      "mobileUrl": [
        "Text"
      ],
      "mpn": [
        "Text"
      ],
      "name": [
        "Text"
      ],
      "offeredBy": [
        "Organization",
        "Person"
      ],
      "owner": [
        "Organization",
        "Person"
      ],
      "potentialAction": [
        "Action"
      ],
      "price": [
        "Number",
        "Text"
      ],
      "priceCurrency": [
        "Text"
      ],
      "priceSpecification": [
        "PriceSpecification"
      ],
      "priceValidUntil": [
        "Date"
      ],
      "review": [
        "Review"
      ],
      "sameAs": [
        "URL"
      ],
      "seller": [
        "Organization",
        "Person"
      ],
      "serialNumber": [
        "Text"
      ],
      "shippingDetails": [
        "OfferShippingDetails"
      ],
      "sku": [
        "Text"
      ],
      "subjectOf": [
        "CreativeWork",
        "Event"
      ],
      "url": [
        "URL"
      ],
      "validForMemberTier": [
        "MemberProgramTier"
      ],
      "validFrom": [
        "Date",
        "DateTime"
      ],
      "validThrough": [
        "Date",
        "DateTime"
      ],
      "warranty": [
        "WarrantyPromise"
      ]
    }
  },
  "Brand": {
    ancestors: [
      "Intangible",
      "Thing"
    ],
    properties: {
      "additionalType": [
        "Text",
        "URL"
      ],
      "aggregateRating": [
        "AggregateRating"
      ],
      "alternateName": [
        "Text"
      ],
      "description": [
        "Text",
        "TextObject"
      ],
      "disambiguatingDescription": [
        "Text"
      ],
      "identifier": [
        "PropertyValue",
        "Text",
        "URL"
      ],
      "image": [
        "ImageObject",
        "URL"
      ],
      "logo": [
        "ImageObject",
        "URL"
      ],
      "mainEntityOfPage": [
        "CreativeWork",
        "URL"
      ],
      "name": [
        "Text"
      ],
      "owner": [
        "Organization",
        "Person"
      ],
      "potentialAction": [
        "Action"
      ],
      "review": [
        "Review"
      ],
      "sameAs": [
        "URL"
      ],
      "slogan": [
        "Text"
      ],
      "subjectOf": [
        "CreativeWork",
        "Event"
      ],
      "url": [
        "URL"
      ]
    }
  },
  "OfferCatalog": {
    ancestors: [
      "ItemList",
      "Intangible",
      "Thing"
    ],
    properties: {
      "additionalType": [
        "Text",
        "URL"
      ],
      "aggregateElement": [
        "Thing"
      ],
      "alternateName": [
        "Text"
      ],
      "description": [
        "Text",
        "TextObject"
      ],
      "disambiguatingDescription": [
        "Text"
      ],
      "identifier": [
        "PropertyValue",
        "Text",
        "URL"
      ],
      "image": [
        "ImageObject",
        "URL"
      ],
      "itemListElement": [
        "ListItem",
        "Text",
        "Thing"
      ],
      "itemListOrder": [
        "ItemListOrderType",
        "Text"
      ],
      "mainEntityOfPage": [
        "CreativeWork",
        "URL"
      ],
      "name": [
        "Text"
      ],
      "numberOfItems": [
        "Integer"
      ],
      "owner": [
        "Organization",
        "Person"
      ],
      "potentialAction": [
        "Action"
      ],
      "sameAs": [
        "URL"
      ],
      "subjectOf": [
        "CreativeWork",
        "Event"
      ],
      "url": [
        "URL"
      ]
    }
  },
  "Organization": {
    ancestors: [
      "Thing"
    ],
    properties: {
      "acceptedPaymentMethod": [
        "LoanOrCredit",
        "PaymentMethod",
        "Text"
      ],
      "actionableFeedbackPolicy": [
        "CreativeWork",
        "URL"
      ],
      "additionalType": [
        "Text",
        "URL"
      ],
      "address": [
        "PostalAddress",
        "Text"
      ],
      "agentInteractionStatistic": [
        "InteractionCounter"
      ],
      "aggregateRating": [
        "AggregateRating"
      ],
      "alternateName": [
        "Text"
      ],
      "alumni": [
        "Person"
      ],
      "areaServed": [
        "AdministrativeArea",
        "GeoShape",
        "Place",
        "Text"
      ],
      "authorizedRepresentative": [
        "Organization",
        "Person"
      ],
      "award": [
        "Text"
      ],
      "brand": [
        "Brand",
        "Organization"
      ],
      "companyRegistration": [
        "Certification"
      ],
      "contactPoint": [
        "ContactPoint"
      ],
      "correctionsPolicy": [
        "CreativeWork",
        "URL"
      ],
      "department": [
        "Organization"
      ],
      "description": [
        "Text",
        "TextObject"
      ],
      "disambiguatingDescription": [
        "Text"
      ],
      "dissolutionDate": [
        "Date"
      ],
      "diversityPolicy": [
        "CreativeWork",
        "URL"
      ],
      "diversityStaffingReport": [
        "Article",
        "URL"
      ],
      "duns": [
        "Text"
      ],
      "email": [
        "Text"
      ],
      "employee": [
        "Person"
      ],
      "ethicsPolicy": [
        "CreativeWork",
        "URL"
      ],
      "event": [
        "Event"
      ],
      "faxNumber": [
        "Text"
      ],
      "founder": [
        "Organization",
        "Person"
      ],
      "foundingDate": [
        "Date"
      ],
      "foundingLocation": [
        "Place"
      ],
      "funder": [
        "Organization",
        "Person"
      ],
      "funding": [
        "Grant"
      ],
      "globalLocationNumber": [
        "Text"
      ],
      "hasCertification": [
        "Certification"
      ],
      "hasCredential": [
        "Credential"
      ],
      "hasGS1DigitalLink": [
        "URL"
      ],
      "hasMemberProgram": [
        "MemberProgram"
      ],
      "hasMerchantReturnPolicy": [
        "MerchantReturnPolicy"
      ],
      "hasOfferCatalog": [
        "OfferCatalog"
      ],
      "hasPOS": [
        "Place"
      ],
      "hasShippingService": [
        "ShippingService"
      ],
      "identifier": [
        "PropertyValue",
        "Text",
        "URL"
      ],
      "image": [
        "ImageObject",
        "URL"
      ],
      "interactionStatistic": [
        "InteractionCounter"
      ],
      "isicV4": [
        "Text"
      ],
      "iso6523Code": [
        "Text"
      ],
      "keywords": [
        "DefinedTerm",
        "Text",
        "URL"
      ],
      "knowsAbout": [
        "Text",
        "Thing",
        "URL"
      ],
      "knowsLanguage": [
        "Language",
        "Text"
      ],
      "legalAddress": [
        "PostalAddress"
      ],
      "legalName": [
        "Text"
      ],
      "legalRepresentative": [
        "Person"
      ],
      "leiCode": [
        "Text"
      ],
      "location": [
        "Place",
        "PostalAddress",
        "Text",
        "VirtualLocation"
      ],
      "logo": [
        "ImageObject",
        "URL"
      ],
      "mainEntityOfPage": [
        "CreativeWork",
        "URL"
      ],
      "makesOffer": [
        "Offer"
      ],
      "member": [
        "Organization",
        "Person"
      ],
      "memberOf": [
        "MemberProgramTier",
        "Organization",
        "ProgramMembership"
      ],
      "naics": [
        "Text"
      ],
      "name": [
        "Text"
      ],
      "nonprofitStatus": [
        "NonprofitType"
      ],
      "numberOfEmployees": [
        "QuantitativeValue"
      ],
      "owner": [
        "Organization",
        "Person"
      ],
      "ownershipFundingInfo": [
        "AboutPage",
        "CreativeWork",
        "Text",
        "URL"
      ],
      "owns": [
        "Thing"
      ],
      "parentOrganization": [
        "Organization"
      ],
      "potentialAction": [
        "Action"
      ],
      "publishingPrinciples": [
        "CreativeWork",
        "URL"
      ],
      "review": [
        "Review"
      ],
      "sameAs": [
        "URL"
      ],
      "seeks": [
        "Demand"
      ],
      "skills": [
        "DefinedTerm",
        "Text"
      ],
      "slogan": [
        "Text"
      ],
      "sponsor": [
        "Organization",
        "Person"
      ],
      "subOrganization": [
        "Organization"
      ],
      "subjectOf": [
        "CreativeWork",
        "Event"
      ],
      "taxID": [
        "Text"
      ],
      "telephone": [
        "Text"
      ],
      "unnamedSourcesPolicy": [
        "CreativeWork",
        "URL"
      ],
      "url": [
        "URL"
      ],
      "vatID": [
        "Text"
      ]
    }
  },
  "PostalAddress": {
    ancestors: [
      "ContactPoint",
      "StructuredValue",
      "Intangible",
      "Thing"
    ],
    properties: {
      "additionalType": [
        "Text",
        "URL"
      ],
      "addressCountry": [
        "Country",
        "Text"
      ],
      "addressLocality": [
        "Text"
      ],
      "addressRegion": [
        "AdministrativeArea",
        "Text"
      ],
      "alternateName": [
        "Text"
      ],
      "areaServed": [
        "AdministrativeArea",
        "GeoShape",
        "Place",
        "Text"
      ],
      "availableLanguage": [
        "Language",
        "Text"
      ],
      "contactOption": [
        "ContactPointOption"
      ],
      "contactType": [
        "Text"
      ],
      "description": [
        "Text",
        "TextObject"
      ],
      "disambiguatingDescription": [
        "Text"
      ],
      "email": [
        "Text"
      ],
      "extendedAddress": [
        "Text"
      ],
      "faxNumber": [
        "Text"
      ],
      "hoursAvailable": [
        "OpeningHoursSpecification"
      ],
      "identifier": [
        "PropertyValue",
        "Text",
        "URL"
      ],
      "image": [
        "ImageObject",
        "URL"
      ],
      "mainEntityOfPage": [
        "CreativeWork",
        "URL"
      ],
      "name": [
        "Text"
      ],
      "owner": [
        "Organization",
        "Person"
      ],
      "postOfficeBoxNumber": [
        "Text"
      ],
      "postalCode": [
        "Text"
      ],
      "potentialAction": [
        "Action"
      ],
      "productSupported": [
        "Product",
        "Text"
      ],
      "sameAs": [
        "URL"
      ],
      "streetAddress": [
        "Text"
      ],
      "subjectOf": [
        "CreativeWork",
        "Event"
      ],
      "telephone": [
        "Text"
      ],
      "url": [
        "URL"
      ]
    }
  }
}

export const enumerations: Record<string, string[]> = {
  ItemAvailability: ["BackOrder", "Discontinued", "InStock", "InStoreOnly", "LimitedAvailability", "MadeToOrder", "OnlineOnly", "OutOfStock", "PreOrder", "PreSale", "Reserved", "SoldOut"],
}
