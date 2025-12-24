require("dotenv").config();
const app = require("./app");
// const { knex } = require("./services/dbService"); // Import Knex if needed for initial check

const PORT = process.env.PORT_BOARD_SERVICE || 3002;

function startServer() {
  app.listen(PORT, () => {
    console.log(`API Gateway Service running on http://localhost:${PORT}`);
    console.log(`Node Environment: ${process.env.NODE_ENV}`);
  });
}

startServer();
