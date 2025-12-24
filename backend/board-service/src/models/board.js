"use strict";
const { Model } = require("sequelize");

module.exports = (sequelize, DataTypes) => {
    class Board extends Model {
        static associate(models) {
            // A board has many columns
            Board.hasMany(models.Column, {
                foreignKey: "board_id",
                as: "columns",
                onDelete: "CASCADE",
                onUpdate: "CASCADE",
            });
        }
    }
    Board.init(
        {
            id: {
                type: DataTypes.UUID,
                defaultValue: DataTypes.UUIDV4,
                primaryKey: true,
            },
            owner_id: {
                type: DataTypes.UUID,
                allowNull: false,
            },
            name: {
                type: DataTypes.STRING(255),
                allowNull: false,
            },
            description: {
                type: DataTypes.TEXT,
                allowNull: true,
            },
            is_public: {
                type: DataTypes.BOOLEAN,
                allowNull: false,
                defaultValue: false,
            },
            created_at: {
                type: DataTypes.DATE,
                allowNull: false,
            },
            updated_at: {
                type: DataTypes.DATE,
                allowNull: false,
            },
        },
        {
            sequelize,
            modelName: "Board",
            tableName: "boards",
            timestamps: true,
            createdAt: "created_at",
            updatedAt: "updated_at",
        }
    );
    return Board;
};