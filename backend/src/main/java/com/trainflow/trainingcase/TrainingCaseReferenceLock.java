package com.trainflow.trainingcase;

import com.trainflow.shared.error.ApiError;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.function.Supplier;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.ConnectionCallback;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/** Serializes reference allocation per year across every application instance using the same MySQL server. */
@Component
class TrainingCaseReferenceLock {
    private static final int LOCK_TIMEOUT_SECONDS = 10;
    private final JdbcTemplate jdbc;
    private final TransactionTemplate transactions;

    TrainingCaseReferenceLock(JdbcTemplate jdbc, PlatformTransactionManager transactionManager) {
        this.jdbc = jdbc;
        this.transactions = new TransactionTemplate(transactionManager);
    }

    <T> T execute(int year, Supplier<T> action) {
        return jdbc.execute((ConnectionCallback<T>) connection -> {
            String lockName = "trainflow:training-case-reference:" + year;
            try (PreparedStatement statement = connection.prepareStatement("select get_lock(?, ?)")) {
                statement.setString(1, lockName);
                statement.setInt(2, LOCK_TIMEOUT_SECONDS);
                try (ResultSet result = statement.executeQuery()) {
                    if (!result.next() || result.getInt(1) != 1) {
                        throw new ApiError(HttpStatus.SERVICE_UNAVAILABLE, "REFERENCE_LOCK_TIMEOUT",
                                "La référence du dossier n’a pas pu être réservée. Réessayez.");
                    }
                }
            }
            try {
                return transactions.execute(status -> action.get());
            } finally {
                try (PreparedStatement statement = connection.prepareStatement("select release_lock(?)")) {
                    statement.setString(1, lockName);
                    statement.executeQuery().close();
                }
            }
        });
    }
}
