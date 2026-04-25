package org.nwdaf.fabricclient;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI ledgerOpenAPI() {
        return new OpenAPI().info(new Info()
            .title("Fabric Client Ledger API")
            .version("1.0")
            .description("Sidecar REST API for recording and querying data-fetch and inference provenance on the Hyperledger Fabric ledger."));
    }
}
