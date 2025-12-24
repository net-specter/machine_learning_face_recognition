// Example Connection Setup (Simplified)
const { Sequelize } = require("sequelize");
const config = require("../config/config.js"); // Your dynamic config file

const env = process.env.NODE_ENV || "development";
const dbConfig = config[env];

const sequelize = new Sequelize(
  dbConfig.database,
  dbConfig.username,
  dbConfig.password,
  {
    host: dbConfig.host,
    dialect: dbConfig.dialect,
    logging: false,
  }
);

module.exports = sequelize;
