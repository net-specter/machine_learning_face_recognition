const { Board, Column } = require("../models");

// Helper: Default columns for a new board
const DEFAULT_COLUMNS = [
    { name: "To Do", position_order: 0 },
    { name: "In Progress", position_order: 1 },
    { name: "Done", position_order: 2 },
];

// POST /boards - Create a new board with default columns
exports.createBoard = async (req, res) => {
    try {
        const { name, description, is_public } = req.body;
        const owner_id = req.user.user_id; // Set by auth middleware

        if (!name) return res.status(400).json({ message: "Board name is required" });

        const board = await Board.create(
            { name, description, is_public, owner_id },
            { returning: true }
        );

        // Create default columns
        const columns = await Promise.all(
            DEFAULT_COLUMNS.map(col =>
                Column.create({
                    board_id: board.id,
                    name: col.name,
                    position_order: col.position_order,
                })
            )
        );

        res.status(201).json({ board, columns });
    } catch (error) {
        res.status(500).json({ message: "Server error", error: error.message });
    }
};

// GET /boards - List all boards for the authenticated user
exports.listBoards = async (req, res) => {
    try {
        const owner_id = req.user.user_id;
        const boards = await Board.findAll({
            where: { owner_id },
            order: [["created_at", "DESC"]],
        });
        res.json(boards);
    } catch (error) {
        res.status(500).json({ message: "Server error", error: error.message });
    }
};

// GET /boards/:id - Get a single board with its columns
exports.getBoard = async (req, res) => {
    try {
        const { id } = req.params;
        const owner_id = req.user.user_id;
        const board = await Board.findOne({
            where: { id, owner_id },
            include: [
                {
                    model: Column,
                    as: "columns",
                    order: [["position_order", "ASC"]],
                },
            ],
        });
        if (!board) return res.status(404).json({ message: "Board not found" });
        res.json(board);
    } catch (error) {
        res.status(500).json({ message: "Server error", error: error.message });
    }
};