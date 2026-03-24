package {{BASE_PACKAGE}}.cucumber;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;

@Component
public class JwtHelper {

    private final SecretKey secretKey;
    private final int expireHours;

    public JwtHelper(
            @Value("${jwt.secret-key:chapter04-test-secret-key-do-not-use-in-production}") String secretKeyString,
            @Value("${jwt.expire-hours:1}") int expireHours) {
        this.secretKey = Keys.hmacShaKeyFor(secretKeyString.getBytes(StandardCharsets.UTF_8));
        this.expireHours = expireHours;
    }

    public String generateToken(String userId) {
        Instant now = Instant.now();
        Instant expiry = now.plus(expireHours, ChronoUnit.HOURS);

        return Jwts.builder()
                .subject(userId)
                .issuedAt(Date.from(now))
                .expiration(Date.from(expiry))
                .signWith(secretKey)
                .compact();
    }

    public String verifyToken(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }
}
