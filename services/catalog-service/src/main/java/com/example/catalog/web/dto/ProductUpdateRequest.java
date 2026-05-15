package com.example.catalog.web.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

public record ProductUpdateRequest(
        @Size(max = 255) String name,
        @Size(max = 2000) String description,
        @Min(0) Integer unitPriceCents,
        @Min(0) Integer stockQuantity) {}
