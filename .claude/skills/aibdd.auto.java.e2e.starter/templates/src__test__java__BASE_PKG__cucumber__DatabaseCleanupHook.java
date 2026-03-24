package {{BASE_PACKAGE}}.cucumber;

import io.cucumber.java.Before;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

public class DatabaseCleanupHook {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private ScenarioContext scenarioContext;

    @Before(order = 0)
    public void cleanDatabase() {
        // Clear ScenarioContext
        scenarioContext.clear();

        // TODO: Add DELETE statements for your tables in correct order
        //       (respect foreign key constraints — delete child tables first)
        // Example:
        // jdbcTemplate.execute("DELETE FROM order_items");
        // jdbcTemplate.execute("DELETE FROM orders");
        // jdbcTemplate.execute("DELETE FROM users");

        // TODO: Reset sequences for your tables
        // Example:
        // jdbcTemplate.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1");
        // jdbcTemplate.execute("ALTER SEQUENCE orders_id_seq RESTART WITH 1");
    }
}
