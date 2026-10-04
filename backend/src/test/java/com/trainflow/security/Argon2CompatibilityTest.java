package com.trainflow.security;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;

class Argon2CompatibilityTest {
    private final Argon2PasswordEncoder encoder = Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8();
    private static final String PWDLIB_HASH = "$argon2id$v=19$m=65536,t=3,p=4$ynwhJv9hRQRasHPqEKEbRw$93QHfMQjLVenCK+G3J3r9FEoUhJB4ch0JWg3KmWGSnc";

    @Test void verifiesExistingPwdlibArgon2idFormat() {
        assertTrue(encoder.matches("Compatibility-Test-Password!42", PWDLIB_HASH));
        assertFalse(encoder.matches("wrong-password", PWDLIB_HASH));
    }
}
