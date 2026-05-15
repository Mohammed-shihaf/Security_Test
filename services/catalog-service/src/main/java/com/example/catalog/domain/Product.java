package com.example.catalog.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import jakarta.persistence.Id;
import java.time.Instant;

@Entity
@Table(
        name = "catalog_products",
        indexes = {@Index(name = "idx_catalog_products_status", columnList = "status")})
public class Product {

    @Id
    @Column(length = 36, nullable = false)
    private String id;

    @Column(nullable = false, length = 64)
    private String sku;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(length = 2000)
    private String description;

    @Column(name = "unit_price_cents", nullable = false)
    private int unitPriceCents;

    @Column(name = "stock_quantity", nullable = false)
    private int stockQuantity;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private ProductStatus status = ProductStatus.ACTIVE;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected Product() {}

    public Product(
            String id,
            String sku,
            String name,
            String description,
            int unitPriceCents,
            int stockQuantity,
            ProductStatus status,
            Instant createdAt,
            Instant updatedAt) {
        this.id = id;
        this.sku = sku;
        this.name = name;
        this.description = description;
        this.unitPriceCents = unitPriceCents;
        this.stockQuantity = stockQuantity;
        this.status = status;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public String getId() {
        return id;
    }

    public String getSku() {
        return sku;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public int getUnitPriceCents() {
        return unitPriceCents;
    }

    public int getStockQuantity() {
        return stockQuantity;
    }

    public ProductStatus getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void applyPatch(String name, String description, Integer unitPriceCents, Integer stockQuantity) {
        if (name != null) {
            this.name = name;
        }
        if (description != null) {
            this.description = description;
        }
        if (unitPriceCents != null) {
            this.unitPriceCents = unitPriceCents;
        }
        if (stockQuantity != null) {
            this.stockQuantity = stockQuantity;
        }
        this.updatedAt = Instant.now();
    }

    public void archive() {
        this.status = ProductStatus.ARCHIVED;
        this.updatedAt = Instant.now();
    }
}
