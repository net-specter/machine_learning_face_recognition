exports.recognizeFace = async (req, res, next) => {
  try {
    return res.status(200).json({ message: "Image is required" });
  } catch (error) {
    next(error);
  }
};
