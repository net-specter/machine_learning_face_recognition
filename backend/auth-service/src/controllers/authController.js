const express = require("express");
const jwt = require("jsonwebtoken");
const { User } = require("../models");
const bcrypt = require("bcryptjs");

const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

// register
exports.register = async (req, res) => {
    try {
        const { full_name, email, phone_number, password } = req.body;
        if (!full_name || !email || !password) {
            return res.status(400).json({ message: "Check Full Name, Email, Password again, you have missed something" });
        }
        const existingUser = await User.findOne({ where: { email } });
        if (existingUser) {
            return res.status(409).json({ message: "Email already registered" });
        }
        const user = await User.create({
            full_name,
            email,
            phone_number,
            password_hash: password,
        });
        return res.status(201).json({ message: "User registered successfully", user_id: user.user_id, email: user.email });
    } catch (error) {
        return res.status(500).json({ message: "Server error", error: error.message });
    }
};

// login
exports.login = async (req, res) => {
    try {
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ message: "Missing email or password" });
        }
        const user = await User.findOne({ where: { email } })
        if (!user) {
            return res.status(401).json({ message: "Invalid email" })
        }
        const valid = await bcrypt.compare(password, user.password_hash);
        if (!valid) {
            return res.status(401).json({ message: "Invalid password" });
        }

        const token = jwt.sign(
            { user_id: user.user_id, email: user.email },
            JWT_SECRET,
            { expiresIn: "1d" }
        );
        res.json({ your_token: token })
    } catch (error) {
        return res.status(500).json({ message: "Server error", error: error.message });
    }
};

// get current user info
exports.me = async (req, res) => {
    try {
        const user = await User.findByPk(req.user.user_id, {
            attributes: ["user_id", "full_name", "email", "phone_number", "created_at", "updated_at"],
        });
        if (!user) {
            return res.status(404).json({ message: "User not found" });
        }
        return res.json(user);
    } catch (error) {
        return res.status(500).json({ message: "Server error", error: error.message });
    }
};


// Get user by ID (for S2S validation)
exports.getUserById = async (req, res) => {
    try {
        const user = await User.findByPk(req.params.user_id, {
            attributes: ["user_id", "full_name", "email", "phone_number", "created_at", "updated_at"],
        });
        if (!user) return res.status(404).json({ message: "User not found" });
        res.json(user);
    } catch (error) {
        res.status(500).json({ message: "Server error", error: error.message });
    }
};
