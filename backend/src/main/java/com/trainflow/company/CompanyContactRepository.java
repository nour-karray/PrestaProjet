package com.trainflow.company;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CompanyContactRepository extends JpaRepository<CompanyContact, UUID> {
    List<CompanyContact> findByCompanyIdOrderByPrimaryDescFullNameAsc(UUID companyId);
    Optional<CompanyContact> findFirstByCompanyIdAndPrimaryTrue(UUID companyId);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("update CompanyContact c set c.primary = false where c.company.id = :companyId and c.primary = true")
    void clearPrimary(@Param("companyId") UUID companyId);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("update CompanyContact c set c.primary = false where c.company.id = :companyId and c.primary = true and c.id <> :exceptId")
    void clearPrimaryExcept(@Param("companyId") UUID companyId, @Param("exceptId") UUID exceptId);
}
