CREATE TABLE catalog_products (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    sku VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(2000),
    unit_price_cents INT NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uk_catalog_products_sku UNIQUE (sku)
);

CREATE INDEX idx_catalog_products_status ON catalog_products (status);
