const express = require("express");
const router = express.Router();
const jwt = require("jsonwebtoken");
const authController = require("../controllers/authController");

const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

// Registration route
router.post("/register", authController.register);

// Login route
router.post("/login", authController.login);

// Get current user info route (protected)
router.get("/me", authMiddleware, authController.me);

// Get user by ID
router.get("/:user_id", authMiddleware, authController.getUserById);

// middleware to verify JWT
function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ message: "Missing or invalid token" });
    }
    const token = authHeader.split(" ")[1];
    try {
        req.user = jwt.verify(token, JWT_SECRET);
        next();
    } catch (error) {
        return res.status(401).json({ message: "Invalid token", error: error.message });
    }
};

module.exports = router;