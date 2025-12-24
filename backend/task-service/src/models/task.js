"use strict";
const { Model } = require("sequelize");

module.exports = (sequelize, DataTypes) => {
    class Task extends Model {
        static associate(models) {
            // A task has many comments
            Task.hasMany(models.Comment, {
                foreignKey: "task_id",
                as: "comments",
                onDelete: "CASCADE",
                onUpdate: "CASCADE",
            });
        }
    }
    Task.init(
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
            column_id: {
                type: DataTypes.UUID,
                allowNull: false,
            },
            title: {
                type: DataTypes.STRING(255),
                allowNull: false,
            },
            description: {
                type: DataTypes.TEXT,
                allowNull: true,
            },
            assigned_user_id: {
                type: DataTypes.UUID,
                allowNull: true,
            },
            creator_user_id: {
                type: DataTypes.UUID,
                allowNull: false,
            },
            position_order: {
                type: DataTypes.INTEGER,
                allowNull: false,
            },
            due_date: {
                type: DataTypes.DATE,
                allowNull: true,
            },
            priority: {
                type: DataTypes.ENUM("Low", "Medium", "High", "Critical"),
                allowNull: false,
                defaultValue: "Medium",
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
            modelName: "Task",
            tableName: "tasks",
            timestamps: true,
            createdAt: "created_at",
            updatedAt: "updated_at",
        }
    );
    return Task;
};