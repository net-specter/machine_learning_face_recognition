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
