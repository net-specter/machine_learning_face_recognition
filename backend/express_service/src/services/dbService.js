// src/services/dbService.js

const knexConfig = require("../../knexfile");
const knex = require("knex")(knexConfig.development);

// Logic to retrieve name
exports.getNameByUuid = async (userUuid) => {
  const user = await knex("users")
    .select("user_name")
    .where("user_uuid", userUuid)
    .first();
  return user ? user.user_name : null;
};

// Logic for Enrollment (saving new user and vector)
exports.enrollNewUser = async (name, featureVector) => {
  const userUuid = require("crypto")
    .randomBytes(16)
    .toString("hex")
    .substring(0, 30);

  // TRANSACTION: Ensures both records are saved or neither are.
  await knex.transaction(async (trx) => {
    await trx("users").insert({ user_uuid: userUuid, user_name: name });
    await trx("feature_vectors").insert({
      user_uuid: userUuid,
      feature_data: JSON.stringify(featureVector), // Store array as JSON string
    });
  });

  return userUuid;
};

module.exports = { ...exports, knex };
