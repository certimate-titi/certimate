package {{BASE_PACKAGE}}.steps.common_then;

import {{BASE_PACKAGE}}.cucumber.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

public class CommonThen {

    @Autowired
    private ScenarioContext scenarioContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("操作成功")
    public void operationSuccessful() {
        ResponseEntity<?> response = scenarioContext.getLastResponse();

        int statusCode = response.getStatusCode().value();
        assertThat(statusCode)
                .as("預期成功（2XX），實際 %d: %s",
                        statusCode,
                        response.getBody())
                .isBetween(200, 299);
    }

    @Then("操作失敗")
    public void operationFailed() {
        ResponseEntity<?> response = scenarioContext.getLastResponse();

        int statusCode = response.getStatusCode().value();
        assertThat(statusCode)
                .as("預期失敗（4XX），實際 %d: %s",
                        statusCode,
                        response.getBody())
                .isBetween(400, 499);
    }

    @SuppressWarnings("unchecked")
    @Then("錯誤訊息應為 {string}")
    public void errorMessageShouldBe(String expectedMessage) throws Exception {
        ResponseEntity<?> response = scenarioContext.getLastResponse();
        Object body = response.getBody();

        String actualMessage = null;

        if (body instanceof String) {
            JsonNode data = objectMapper.readTree((String) body);
            if (data.has("message")) {
                actualMessage = data.get("message").asText();
            } else if (data.has("detail")) {
                actualMessage = data.get("detail").asText();
            } else if (data.has("error")) {
                actualMessage = data.get("error").asText();
            }
        } else if (body instanceof java.util.Map) {
            java.util.Map<String, Object> map = (java.util.Map<String, Object>) body;
            if (map.containsKey("message")) {
                actualMessage = String.valueOf(map.get("message"));
            } else if (map.containsKey("detail")) {
                actualMessage = String.valueOf(map.get("detail"));
            } else if (map.containsKey("error")) {
                actualMessage = String.valueOf(map.get("error"));
            }
        }

        assertThat(actualMessage)
                .as("預期錯誤訊息 '%s'，實際 '%s'", expectedMessage, actualMessage)
                .isEqualTo(expectedMessage);
    }

    @Then("操作失敗，原因為 {string}")
    public void operationFailedWithReason(String reason) throws Exception {
        operationFailed();
        errorMessageShouldBe(reason);
    }
}
