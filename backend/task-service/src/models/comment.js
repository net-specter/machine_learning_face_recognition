"use strict";
const { Model } = require("sequelize");

module.exports = (sequelize, DataTypes) => {
    class Comment extends Model {
        static associate(models) {
            // A comment belongs to a task
            Comment.belongsTo(models.Task, {
                foreignKey: "task_id",
                as: "task",
                onDelete: "CASCADE",
                onUpdate: "CASCADE",
            });
        }
    }
    Comment.init(
        {
            id: {
                type: DataTypes.UUID,
                defaultValue: DataTypes.UUIDV4,
                primaryKey: true,
            },
            task_id: {
                type: DataTypes.UUID,
                allowNull: false,
            },  
            user_id: {
                type: DataTypes.UUID,
                allowNull: false,
            },
            content: {
                type: DataTypes.TEXT,
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
            modelName: "Comment",
            tableName: "comments",
            timestamps: true,
            createdAt: "created_at",
            updatedAt: "updated_at",
        }
    );
    return Comment;
};