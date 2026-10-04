package com.trainflow.security;

import com.trainflow.auth.Administrator;
import com.trainflow.auth.AdministratorRepository;
import java.util.UUID;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class CustomUserDetailsService implements UserDetailsService {
    private final AdministratorRepository administrators;
    public CustomUserDetailsService(AdministratorRepository administrators) { this.administrators = administrators; }
    @Override public UserDetails loadUserByUsername(String email) {
        return user(administrators.findByEmailIgnoreCase(email).orElseThrow(() -> new UsernameNotFoundException("Administrateur introuvable.")));
    }
    public UserDetails loadById(UUID id) {
        return user(administrators.findById(id).orElseThrow(() -> new UsernameNotFoundException("Administrateur introuvable.")));
    }
    private UserDetails user(Administrator administrator) {
        return User.withUsername(administrator.getId().toString()).password(administrator.getPasswordHash())
                .authorities("ROLE_ADMIN").disabled(!administrator.isActive()).build();
    }
}
