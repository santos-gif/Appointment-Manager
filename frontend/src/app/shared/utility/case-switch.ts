const toSnakeCase = (str: string) =>
  str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);

const toCamelCase = (str: string) =>
  str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
