package com.example.catalog.service;

import com.example.catalog.domain.Product;
import com.example.catalog.domain.ProductStatus;
import com.example.catalog.repo.ProductRepository;
import com.example.catalog.web.dto.ProductCreateRequest;
import com.example.catalog.web.dto.ProductResponse;
import com.example.catalog.web.dto.ProductUpdateRequest;
import com.example.catalog.web.error.ResourceNotFoundException;
import java.time.Instant;
import java.util.UUID;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class CatalogService {

    private final ProductRepository products;

    public CatalogService(ProductRepository products) {
        this.products = products;
    }

    @Transactional(readOnly = true)
    public Page<ProductResponse> listActive(Pageable pageable) {
        return products.findByStatus(ProductStatus.ACTIVE, pageable).map(ProductResponse::from);
    }

    @Transactional(readOnly = true)
    public Page<ProductResponse> search(String rawQuery, Pageable pageable) {
        if (rawQuery == null || rawQuery.isBlank()) {
            return listActive(pageable);
        }
        String needle = "%" + rawQuery.trim().toLowerCase() + "%";
        return products.searchVisible(needle, ProductStatus.ACTIVE, pageable).map(ProductResponse::from);
    }

    @Transactional(readOnly = true)
    @Cacheable(cacheNames = "productsById", key = "#id", unless = "#result == null")
    public ProductResponse get(String id) {
        return products.findById(id).map(ProductResponse::from).orElseThrow(() -> unknown(id));
    }

    @CacheEvict(cacheNames = {"productsById", "productSummaries"}, allEntries = true)
    public ProductResponse create(ProductCreateRequest req) {
        products.findBySkuIgnoreCase(req.sku()).ifPresent(existing -> {
            throw new IllegalArgumentException("SKU already exists: " + req.sku());
        });
        Instant now = Instant.now();
        Product entity =
                new Product(
                        UUID.randomUUID().toString(),
                        req.sku().trim(),
                        req.name().trim(),
                        req.description() != null ? req.description().trim() : null,
                        req.unitPriceCents(),
                        req.stockQuantity(),
                        ProductStatus.ACTIVE,
                        now,
                        now);
        return ProductResponse.from(products.save(entity));
    }

    @CacheEvict(cacheNames = {"productsById", "productSummaries"}, key = "#id")
    public ProductResponse update(String id, ProductUpdateRequest req) {
        Product entity = products.findById(id).orElseThrow(() -> unknown(id));
        if (entity.getStatus() != ProductStatus.ACTIVE) {
            throw new IllegalStateException("Cannot modify archived product: " + id);
        }
        entity.applyPatch(req.name(), req.description(), req.unitPriceCents(), req.stockQuantity());
        return ProductResponse.from(products.save(entity));
    }

    @CacheEvict(cacheNames = {"productsById", "productSummaries"}, key = "#id")
    public ProductResponse archive(String id) {
        Product entity = products.findById(id).orElseThrow(() -> unknown(id));
        entity.archive();
        return ProductResponse.from(products.save(entity));
    }

    private static ResourceNotFoundException unknown(String id) {
        return new ResourceNotFoundException("Product not found: " + id);
    }
}
