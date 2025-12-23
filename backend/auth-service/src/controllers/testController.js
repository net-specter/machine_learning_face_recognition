exports.test = async (req, res, next) => {
  try {
    return res.status(200).json({ message: "This is test message" });
  } catch (error) {
    next(error);
  }
};
