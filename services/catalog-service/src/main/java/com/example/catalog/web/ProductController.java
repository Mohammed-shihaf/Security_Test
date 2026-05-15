package com.example.catalog.web;

import com.example.catalog.service.CatalogService;
import com.example.catalog.web.dto.ProductCreateRequest;
import com.example.catalog.web.dto.ProductResponse;
import com.example.catalog.web.dto.ProductUpdateRequest;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/api/v1/products")
@Tag(name = "Catalog products", description = "Sample CRUD surface for static/JVM tooling.")
public class ProductController {

    private final CatalogService catalog;

    public ProductController(CatalogService catalog) {
        this.catalog = catalog;
    }

    @GetMapping
    @Operation(summary = "List or search active catalog products")
    public Page<ProductResponse> list(
            @RequestParam(required = false) String q,
            @PageableDefault(size = 20) Pageable pageable) {
        return catalog.search(q, pageable);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Fetch one product by id")
    public ProductResponse get(@PathVariable String id) {
        return catalog.get(id);
    }

    @PostMapping
    @Operation(summary = "Create a product")
    public ResponseEntity<ProductResponse> create(@Valid @RequestBody ProductCreateRequest body) {
        ProductResponse created = catalog.create(body);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Patch mutable fields on an active product")
    public ProductResponse update(@PathVariable String id, @Valid @RequestBody ProductUpdateRequest body) {
        return catalog.update(id, body);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Archive a product (soft delete)")
    public ProductResponse archive(@PathVariable String id) {
        return catalog.archive(id);
    }
}
