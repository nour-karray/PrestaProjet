package com.trainflow.program;

import java.util.function.Supplier;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

@Component
class ProgramGenerationTransactions {
    private final TransactionTemplate read;
    private final TransactionTemplate write;

    ProgramGenerationTransactions(PlatformTransactionManager manager) {
        read = new TransactionTemplate(manager);
        read.setReadOnly(true);
        write = new TransactionTemplate(manager);
    }

    <T> T read(Supplier<T> action) { return read.execute(status -> action.get()); }
    <T> T write(Supplier<T> action) { return write.execute(status -> action.get()); }
}
