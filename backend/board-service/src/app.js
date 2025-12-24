// src/app.js (Defines the Express App)

const express = require("express");
const cors = require("cors");
const morgan = require("morgan");

const app = express();

app.use(cors());
app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ extended: true, limit: "50mb" }));
app.use(morgan("dev"));

// route registration
const testRoutes = require("./routers/testRoutes");
app.use("/api/v1", testRoutes);
const boardRoutes = require("./routers/boardRoutes");
app.use("/api/v1", boardRoutes);

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    message: err.message || "Internal Server Error",
    status: err.status || 500,
  });
});

module.exports = app;
