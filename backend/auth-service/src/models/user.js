"use strict";
const { Model } = require("sequelize");
const bcrypt = require("bcryptjs");

module.exports = (sequelize, DataTypes) => {
  class User extends Model {
    static associate(models) {
      // Only create associations if the target models exist to avoid startup errors
      //   if (models.Role) {
      //     User.belongsToMany(models.Role, {
      //       through: "UserRoles",
      //       foreignKey: "user_id",
      //       otherKey: "role_id",
      //       as: "Roles",
      //     });
      //   }
    }

    async comparePassword(password) {
      return bcrypt.compare(password, this.password_hash);
    }
  }
  User.init(
    {
      user_id: {
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true,
      },
      full_name: { type: DataTypes.STRING(255), allowNull: false },
      email: {
        type: DataTypes.STRING(191),
        allowNull: false,
        unique: true,
        validate: { isEmail: true },
      },
      phone_number: {
        // Matches your SQL email
        type: DataTypes.STRING(191),
        allowNull: false,
        // unique: true,
        validate: {
          is: /^[0-9+\-() ]+$/i, // Basic phone number validation
        },
      },
      password_hash: { type: DataTypes.STRING(255), allowNull: false },
    },
    {
      sequelize,
      modelName: "User",
      tableName: "Users",
      timestamps: true,
      paranoid: false,
      createdAt: "created_at",
      updatedAt: "updated_at",
      hooks: {
        beforeCreate: async (user) => {
          if (user.password_hash) {
            user.password_hash = await bcrypt.hash(user.password_hash, 10);
          }
        },
        beforeUpdate: async (user) => {
          if (user.changed("password_hash") && user.password_hash) {
            user.password_hash = await bcrypt.hash(user.password_hash, 10);
          }
        },
      },
    }
  );
  return User;
};
