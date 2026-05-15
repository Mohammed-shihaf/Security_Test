package com.example.catalog.web;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;

import com.jayway.jsonpath.JsonPath;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class ProductApiIntegrationTest {

    @Autowired MockMvc mvc;

    @Test
    void create_list_get_update_archive_flow() throws Exception {
        String body =
                """
                {"sku":"SKU-LAB-1","name":"Widget","description":"Harness SKU","unitPriceCents":199,"stockQuantity":10}
                """;

        String created =
                mvc.perform(post("/api/v1/products").contentType(MediaType.APPLICATION_JSON).content(body))
                        .andExpect(status().isCreated())
                        .andExpect(jsonPath("$.sku").value("SKU-LAB-1"))
                        .andExpect(jsonPath("$.name").value("Widget"))
                        .andReturn()
                        .getResponse()
                        .getContentAsString();

        String id = JsonPath.read(created, "$.id");

        mvc.perform(get("/api/v1/products").param("q", "widget"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)));

        String patch = "{\"name\":\"Widget Pro\",\"unitPriceCents\":249}";
        mvc.perform(
                        put("/api/v1/products/" + id)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(patch))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Widget Pro"))
                .andExpect(jsonPath("$.unitPriceCents").value(249));

        mvc.perform(delete("/api/v1/products/" + id)).andExpect(status().isOk());

        mvc.perform(get("/api/v1/products/" + id)).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("ARCHIVED"));
    }

    @Test
    void duplicateSku_returns400() throws Exception {
        String body =
                """
                {"sku":"SKU-DUP","name":"A","description":null,"unitPriceCents":1,"stockQuantity":0}
                """;
        mvc.perform(post("/api/v1/products").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isCreated());
        mvc.perform(post("/api/v1/products").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message", containsString("SKU already exists")));
    }

    @Test
    void unknownProduct_returns404() throws Exception {
        mvc.perform(get("/api/v1/products/00000000-0000-0000-0000-000000000000"))
                .andExpect(status().isNotFound());
    }

    @Test
    void validationError_returns400() throws Exception {
        String bad = "{\"sku\":\"\",\"name\":\"\",\"unitPriceCents\":-1,\"stockQuantity\":0}";
        mvc.perform(post("/api/v1/products").contentType(MediaType.APPLICATION_JSON).content(bad))
                .andExpect(status().isBadRequest());
    }
}
