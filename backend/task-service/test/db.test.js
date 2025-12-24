// backend/task-service/tests/db.test.js
const sequelize = require("../config/database"); // Import your sequelize instance

// We use describe and test functions provided by Jest
describe("Task Service Integration Tests", () => {
  // Test 1: Verify the database connection is successful
  test("should successfully authenticate the database connection", async () => {
    try {
      // Sequelize's authenticate() method attempts to connect to the DB
      // It uses the environment variables DB_HOST, DB_USER, etc., set in the CI pipeline.
      await sequelize.authenticate();
      console.log("Database connection authenticated successfully.");
      expect(true).toBe(true); // If it reaches here, success!
    } catch (error) {
      console.error("Database Connection Failed:", error.message);
      // If the connection fails, the test fails
      fail("Failed to connect to the temporary MySQL instance.");
    }
  });

  // Test 2: Verify a basic read/write operation (Optional, requires a Task Model)
  // Assuming you have a Task model defined and exported via sequelize
  /*
  test('should allow creating and finding a new task', async () => {
    // 1. Setup/Cleanup (before starting the test)
    await sequelize.sync({ force: true }); // Resets the database table

    // 2. Perform the write operation
    const testTask = await sequelize.models.Task.create({
      title: 'CI Pipeline Test Task',
      boardId: 'B-TEST', // Use a mock ID
      status: 'To Do'
    });

    // 3. Perform the read operation
    const fetchedTask = await sequelize.models.Task.findByPk(testTask.id);

    // 4. Assertions
    expect(fetchedTask).toBeDefined();
    expect(fetchedTask.title).toBe('CI Pipeline Test Task');
  });
  */

  // Optional: Close the connection after all tests are done
  afterAll(async () => {
    await sequelize.close();
  });
});
