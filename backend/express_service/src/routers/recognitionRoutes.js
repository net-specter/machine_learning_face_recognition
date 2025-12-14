const express = require("express");
const router = express.Router();
const recognitionController = require("../controllers/recognitionController");

router.get("/recognize", recognitionController.recognizeFace);
// router.post("/enroll", recognitionController.enrollUser);

module.exports = router;
