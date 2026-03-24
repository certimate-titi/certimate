package {{BASE_PACKAGE}}.cucumber;

import io.cucumber.spring.ScenarioScope;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Component
@ScenarioScope
public class ScenarioContext {

    private ResponseEntity<?> lastResponse;
    private final Map<String, Object> ids = new HashMap<>();
    private final Map<String, Object> memo = new HashMap<>();
    private String jwtToken;
    private Object queryResult;
    private String lastError;

    public ResponseEntity<?> getLastResponse() {
        return lastResponse;
    }

    public void setLastResponse(ResponseEntity<?> lastResponse) {
        this.lastResponse = lastResponse;
    }

    public Map<String, Object> getIds() {
        return ids;
    }

    public void putId(String key, Object value) {
        ids.put(key, value);
    }

    @SuppressWarnings("unchecked")
    public <T> T getId(String key) {
        return (T) ids.get(key);
    }

    public boolean hasId(String key) {
        return ids.containsKey(key);
    }

    public Map<String, Object> getMemo() {
        return memo;
    }

    public void putMemo(String key, Object value) {
        memo.put(key, value);
    }

    @SuppressWarnings("unchecked")
    public <T> T getMemo(String key) {
        return (T) memo.get(key);
    }

    public String getJwtToken() {
        return jwtToken;
    }

    public void setJwtToken(String jwtToken) {
        this.jwtToken = jwtToken;
    }

    public Object getQueryResult() {
        return queryResult;
    }

    public void setQueryResult(Object queryResult) {
        this.queryResult = queryResult;
    }

    public String getLastError() {
        return lastError;
    }

    public void setLastError(String lastError) {
        this.lastError = lastError;
    }

    public void clear() {
        this.lastResponse = null;
        this.ids.clear();
        this.memo.clear();
        this.jwtToken = null;
        this.queryResult = null;
        this.lastError = null;
    }
}
