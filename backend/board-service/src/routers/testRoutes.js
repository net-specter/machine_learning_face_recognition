const express = require("express");
const router = express.Router();
const recognitionController = require("../controllers/testController");

router.get("/test", recognitionController.test);

module.exports = router;
