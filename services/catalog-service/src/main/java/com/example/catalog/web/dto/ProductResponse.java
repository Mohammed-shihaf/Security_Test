package com.example.catalog.web.dto;

import com.example.catalog.domain.Product;
import com.example.catalog.domain.ProductStatus;
import java.time.Instant;

public record ProductResponse(
        String id,
        String sku,
        String name,
        String description,
        int unitPriceCents,
        int stockQuantity,
        ProductStatus status,
        Instant createdAt,
        Instant updatedAt) {

    public static ProductResponse from(Product entity) {
        return new ProductResponse(
                entity.getId(),
                entity.getSku(),
                entity.getName(),
                entity.getDescription(),
                entity.getUnitPriceCents(),
                entity.getStockQuantity(),
                entity.getStatus(),
                entity.getCreatedAt(),
                entity.getUpdatedAt());
    }
}
