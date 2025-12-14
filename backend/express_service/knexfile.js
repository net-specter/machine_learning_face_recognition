// knexfile.js
require("dotenv").config({ path: "./.env" }); // Load .env file

module.exports = {
  development: {
    client: "pg",
    connection: {
      host: process.env.PG_HOST,
      port: process.env.PG_PORT,
      user: process.env.PG_USER,
      password: process.env.PG_PASSWORD,
      database: process.env.PG_DATABASE,
    },
    migrations: {
      directory: "./src/migrations", // Where migration files will live
    },
    seeds: {
      directory: "./src/seeders", // Optional: for inserting initial data
    },
  },
  // Production and Staging configurations would go here
};
