module.exports = {
  development: {
    // These must match the variables supplied by docker-compose
    username: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    host: process.env.DB_HOST,
    dialect: "mysql",
  },
  test: {
    // Use separate variables or default to development for tests
    username: process.env.TEST_DB_USER || process.env.DB_USER,
    password: process.env.TEST_DB_PASSWORD || process.env.DB_PASSWORD,
    database: process.env.TEST_DB_NAME || process.env.DB_NAME,
    host: process.env.TEST_DB_HOST || process.env.DB_HOST,
    dialect: "mysql",
  },
  production: {
    // Production will use the host provided by Render
    username: process.env.PROD_DB_USER,
    password: process.env.PROD_DB_PASSWORD,
    database: process.env.PROD_DB_NAME,
    host: process.env.PROD_DB_HOST,
    dialect: "mysql",
  },
};
