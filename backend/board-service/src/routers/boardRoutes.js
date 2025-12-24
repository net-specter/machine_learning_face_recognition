const express = require("express");
const router = express.Router();
const boardController = require("../controllers/boardController");

// Create board
router.post("/boards", authMiddleware, boardController.createBoard);

// List boards
router.get("/boards", authMiddleware, boardController.listBoards);

// Get single board with columns
router.get("/boards/:id", authMiddleware, boardController.getBoard);

const jwt = require("jsonwebtoken");
const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

function authMiddleware (req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ message: "Missing token" });
    const token = authHeader.split(" ")[1];
    try {
        req.user = jwt.verify(token, JWT_SECRET);
        next();
    } catch (err) {
        res.status(401).json({ message: "Invalid token" });
    }
};

module.exports = router;