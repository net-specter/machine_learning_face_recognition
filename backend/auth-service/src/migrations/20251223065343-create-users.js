"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => {
    await queryInterface.createTable("Users", {
      user_id: {
        // Use UUID primary key
        allowNull: false,
        primaryKey: true,
        type: Sequelize.UUID,
        defaultValue: Sequelize.UUIDV4,
      },
      full_name: {
        // Matches your SQL full_name
        type: Sequelize.STRING(255),
        allowNull: false,
      },
      email: {
        // Matches your SQL email
        type: Sequelize.STRING(191),
        allowNull: false,
        unique: true,
        validate: {
          isEmail: true, // Sequelize validation
        },
      },
      phone_number: {
        // Matches your SQL email
        type: Sequelize.STRING(191),
        allowNull: false,
        // unique: true,
        validate: {
          is: /^[0-9+\-() ]+$/i, // Basic phone number validation
        },
      },
      password_hash: {
        // Matches your SQL password_hash
        type: Sequelize.STRING(255),
        allowNull: false,
      },

      created_at: {
        allowNull: false,
        type: Sequelize.DATE,
        defaultValue: Sequelize.literal("CURRENT_TIMESTAMP"),
      },
      updated_at: {
        allowNull: false,
        type: Sequelize.DATE,
        defaultValue: Sequelize.literal(
          "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        ),
      },
    });
  },

  down: async (queryInterface, Sequelize) => {
    await queryInterface.dropTable("Users");
  },
};
