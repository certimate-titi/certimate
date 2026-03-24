package {{BASE_PACKAGE}}.security;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

public class CurrentUser {

    public static Long getId(HttpServletRequest request) {
        Object userId = request.getAttribute(JwtTokenFilter.CURRENT_USER_ID_ATTRIBUTE);
        if (userId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "無效的認證憑證");
        }
        return (Long) userId;
    }

    public static Long getIdOrNull(HttpServletRequest request) {
        Object userId = request.getAttribute(JwtTokenFilter.CURRENT_USER_ID_ATTRIBUTE);
        return userId != null ? (Long) userId : null;
    }
}
