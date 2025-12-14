// db/migrations/[timestamp]_create_initial_schema.js

exports.up = function (knex) {
  // UP: Defines how to create the tables
  return knex.schema
    .createTable("users", (table) => {
      table.increments("user_id").primary(); // user_id SERIAL PRIMARY KEY
      table.string("user_uuid", 50).unique().notNullable();
      table.string("user_name", 100).notNullable();
      table.timestamp("created_at").defaultTo(knex.fn.now());
    })
    .createTable("feature_vectors", (table) => {
      table.increments("vector_id").primary();
      // Foreign Key pointing to the users table
      table
        .string("user_uuid", 50)
        .references("user_uuid")
        .inTable("users")
        .onDelete("CASCADE");
      table.text("feature_data").notNullable(); // Stores the vector array as JSON string/Text
      table.timestamp("created_at").defaultTo(knex.fn.now());
    });
};

exports.down = function (knex) {
  // DOWN: Defines how to safely undo the changes (rollback)
  return knex.schema.dropTable("feature_vectors").dropTable("users");
};
