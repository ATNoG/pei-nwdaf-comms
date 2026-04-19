package org.nwdaf.fabricclient.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.nwdaf.fabricclient.FabricGatewayService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/ledger")
@ConditionalOnProperty(name = "dlt.debug", havingValue = "true")
@Tag(name = "Ledger (Debug)", description = "Debug-only endpoints — active only when dlt.debug=true")
public class DebugLedgerController {

    private final FabricGatewayService fabric;

    public DebugLedgerController(FabricGatewayService fabric) {
        this.fabric = fabric;
    }

    @Operation(
        summary = "[DEBUG] List all analytics records",
        description = "Returns every data-fetch record on the ledger. Unbounded — use only for debugging on small datasets.",
        responses = {
            @ApiResponse(responseCode = "200", description = "JSON array of all analytics records",
                content = @Content(schema = @Schema(type = "string")))
        }
    )
    @GetMapping("/analytics")
    public ResponseEntity<String> getAllAnalytics() throws Exception {
        return ResponseEntity.ok(fabric.getAllDataFetches());
    }

    @Operation(
        summary = "[DEBUG] List all inference records",
        description = "Returns every inference record on the ledger. Unbounded — use only for debugging on small datasets.",
        responses = {
            @ApiResponse(responseCode = "200", description = "JSON array of all inference records",
                content = @Content(schema = @Schema(type = "string")))
        }
    )
    @GetMapping("/inference")
    public ResponseEntity<String> getAllInferences() throws Exception {
        return ResponseEntity.ok(fabric.getAllInferences());
    }
}
