package com.example.catalog.repo;

import com.example.catalog.domain.Product;
import com.example.catalog.domain.ProductStatus;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ProductRepository extends JpaRepository<Product, String>, JpaSpecificationExecutor<Product> {

    Optional<Product> findBySkuIgnoreCase(String sku);

    @Query(
            """
            SELECT p FROM Product p
            WHERE p.status = :status
              AND (
                    LOWER(p.name) LIKE :needle
                 OR LOWER(p.sku) LIKE :needle
                 OR LOWER(COALESCE(p.description, '')) LIKE :needle
              )
            """)
    Page<Product> searchVisible(
            @Param("needle") String needle, @Param("status") ProductStatus status, Pageable pageable);

    Page<Product> findByStatus(ProductStatus status, Pageable pageable);
}
