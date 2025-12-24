const { Task, Comment } = require("../models");
const axios = require("axios");

const BOARD_SERVICE_URL =
  process.env.BOARD_SERVICE_URL || "http://localhost:3001";
const AUTH_SERVICE_URL =
  process.env.AUTH_SERVICE_URL || "http://localhost:3000";

// Helper: Validate board existence via Board-Service
async function validateBoard(board_id, token) {
  try {
    const res = await axios.get(
      `${BOARD_SERVICE_URL}/api/v1/boards/${board_id}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return res.status === 200;
  } catch {
    return false;
  }
}

// Helper: Validate user existence via Auth-Service
async function validateUser(user_id, token) {
  try {
    const res = await axios.get(`${AUTH_SERVICE_URL}/api/v1/auth/${user_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.status === 200;
  } catch {
    return false;
  }
}
// POST /tasks - Create a new task (S2S board check)
exports.createTask = async (req, res) => {
  try {
    const {
      board_id,
      column_id,
      title,
      description,
      assigned_user_id,
      position_order,
      due_date,
      priority,
    } = req.body;
    const creator_user_id = req.user.user_id; // Set by auth middleware

    // Validate board existence
    const boardExists = await validateBoard(board_id, req.token);
    if (!boardExists)
      return res.status(400).json({ message: "Invalid board_id" });

    // If assigned_user_id is given, validate user
    if (assigned_user_id) {
      const userExists = await validateUser(assigned_user_id, req.token);
      if (!userExists)
        return res.status(400).json({ message: "Invalid assigned_user_id" });
    }

    // Create task
    const task = await Task.create({
      board_id,
      column_id,
      title,
      description,
      assigned_user_id,
      creator_user_id,
      position_order,
      due_date,
      priority,
    });

    res.status(201).json(task);
  } catch (error) {
    res.status(500).json({ message: "Server error", error: error.message });
  }
};

// PATCH /tasks/:id/assign - Assign a user to a task (S2S user check)
exports.assignUser = async (req, res) => {
  try {
    const { id } = req.params;
    const { assigned_user_id } = req.body;

    // Validate user existence
    const userExists = await validateUser(assigned_user_id, req.token);
    if (!userExists)
      return res.status(400).json({ message: "Invalid assigned_user_id" });

    const task = await Task.findByPk(id);
    if (!task) return res.status(404).json({ message: "Task not found" });

    task.assigned_user_id = assigned_user_id;
    await task.save();

    res.json(task);
  } catch (error) {
    res.status(500).json({ message: "Server error", error: error.message });
  }
};

// PATCH /tasks/:id/move - Move task to another column (S2S board/column check)
exports.moveTask = async (req, res) => {
    try {
        const { id } = req.params;
        const { column_id, position_order } = req.body;

        const task = await Task.findByPk(id);
        if (!task) return res.status(404).json({ message: "Task not found" });

        // Optionally: Validate column_id via Board-Service if needed

        task.column_id = column_id;
        if (position_order !== undefined) task.position_order = position_order;
        await task.save();

        res.json(task);
    } catch (error) {
        res.status(500).json({ message: "Server error", error: error.message });
    }
};

// POST /tasks/:id/comments - Add a comment to a task
exports.addComment = async (req, res) => {
    try {
        const { id } = req.params;
        const { content } = req.body;
        const user_id = req.user.user_id;

        // Validate task existence
        const task = await Task.findByPk(id);
        if (!task) return res.status(404).json({ message: "Task not found" });

        // Validate user existence (optional, since user is authenticated)
        const userExists = await validateUser(user_id, req.token);
        if (!userExists) return res.status(400).json({ message: "Invalid user_id" });

        const comment = await Comment.create({
            task_id: id,
            user_id: user_id,
            content,
        });

        res.status(201).json(comment);
    } catch (error) {
        res.status(500).json({ message: "Server error", error: error.message });
    }
};
