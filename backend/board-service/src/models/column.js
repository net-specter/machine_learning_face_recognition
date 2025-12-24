"use strict";
const { Model } = require("sequelize");

module.exports = (sequelize, DataTypes) => {
    class Column extends Model {
        static associate(models) {
            // A column belongs to a board
            Column.belongsTo(models.Board, {
                foreignKey: "board_id",
                as: "board",
                onDelete: "CASCADE",
                onUpdate: "CASCADE",
            });
        }
    }
    Column.init(
        {
            id: {
                type: DataTypes.UUID,
                defaultValue: DataTypes.UUIDV4,
                primaryKey: true,
            },
            board_id: {
                type: DataTypes.UUID,
                allowNull: false,
            },
            name: {
                type: DataTypes.STRING(255),
                allowNull: false,
            },
            position_order: {
                type: DataTypes.INTEGER,
                allowNull: false,
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
            modelName: "Column",
            tableName: "columns",
            timestamps: true,
            createdAt: "created_at",
            updatedAt: "updated_at",
        }
    );
    return Column;
};