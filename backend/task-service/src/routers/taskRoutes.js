const express = require("express");
const router = express.Router();
const taskController = require("../controllers/taskController");

// Create task
router.post("/tasks", authMiddleware, taskController.createTask);

// Assign user to task
router.patch("/tasks/:id/assign", authMiddleware, taskController.assignUser);

// Move task to another column
router.patch("/tasks/:id/move", authMiddleware, taskController.moveTask);

// Add comment to task
router.post("/tasks/:id/comments", authMiddleware, taskController.addComment);

const jwt = require("jsonwebtoken");
const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ message: "Missing token" });
    const token = authHeader.split(" ")[1];
    try {
        req.user = jwt.verify(token, JWT_SECRET);
        req.token = token; // Pass token for S2S calls
        next();
    } catch (err) {
        res.status(401).json({ message: "Invalid token" });
    }
};

module.exports = router;