package org.nwdaf.fabricclient.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.hyperledger.fabric.client.GatewayException;
import org.nwdaf.fabricclient.FabricGatewayService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/ledger")
@Tag(name = "Ledger", description = "Hyperledger Fabric ledger operations for analytics and inference provenance")
public class LedgerController {

    private final FabricGatewayService fabric;

    public LedgerController(FabricGatewayService fabric) {
        this.fabric = fabric;
    }

    // ── Analytics (data-fetch) ────────────────────────────────────────────

    @Schema(description = "Request body for recording an analytics (data-fetch) event on the ledger")
    record AnalyticsRequest(
        @Schema(description = "Unique request identifier", example = "df-001") @NotBlank String requestId,
        @Schema(description = "MLflow run ID that triggered this fetch", example = "abc123def456") @NotBlank String mlflowRunId,
        @Schema(description = "Model name", example = "anomaly-detector") @NotBlank String modelName,
        @Schema(description = "Model version", example = "3") @NotBlank String modelVersion,
        @Schema(description = "GROQ/descriptor string identifying the query", example = "ue_stats:5g:city=porto") @NotBlank String queryDescriptor,
        @Schema(description = "SHA-256 hash of fetched data", example = "e3b0c44298fc1c149afb") @NotBlank String dataHash,
        @Schema(description = "Comma-separated cell IDs, nullable", example = "cell-1,cell-2") String extraIds,
        @Schema(description = "ISO-8601 start of time range", example = "2024-01-01T00:00:00Z") String timeRangeStart,
        @Schema(description = "ISO-8601 end of time range", example = "2024-01-02T00:00:00Z") String timeRangeEnd
    ) {}

    @Operation(
        summary = "Record an analytics event",
        description = "Submits a data-fetch provenance record to the Fabric ledger. Returns the transaction ID.",
        responses = {
            @ApiResponse(responseCode = "200", description = "Transaction ID of the submitted record",
                content = @Content(schema = @Schema(type = "string", example = "txid-abc123"))),
            @ApiResponse(responseCode = "400", description = "Validation error — required fields missing or blank")
        }
    )
    @PostMapping("/analytics")
    public ResponseEntity<String> recordAnalytics(@Valid @RequestBody AnalyticsRequest req)
                                                   throws Exception {
        String result = fabric.recordDataFetch(
            req.requestId(), req.mlflowRunId(), req.modelName(), req.modelVersion(),
            req.queryDescriptor(), req.dataHash(),
            req.extraIds(), req.timeRangeStart(), req.timeRangeEnd());
        return ResponseEntity.ok(result);
    }

    @Operation(
        summary = "Get an analytics record by request ID",
        responses = {
            @ApiResponse(responseCode = "200", description = "JSON-encoded ledger record",
                content = @Content(schema = @Schema(type = "string"))),
            @ApiResponse(responseCode = "404", description = "Record not found")
        }
    )
    @GetMapping("/analytics/{requestId}")
    public ResponseEntity<String> getAnalytics(
            @Parameter(description = "Request ID used when the record was created", example = "df-001")
            @PathVariable String requestId) throws Exception {
        try {
            return ResponseEntity.ok(fabric.getDataFetchRecord(requestId));
        } catch (GatewayException e) {
            if (isNotFound(e)) return ResponseEntity.notFound().build();
            throw e;
        }
    }

    @Operation(
        summary = "List analytics records by MLflow run ID",
        description = "Returns all data-fetch records associated with a given MLflow run.",
        responses = {
            @ApiResponse(responseCode = "200", description = "JSON array of ledger records",
                content = @Content(schema = @Schema(type = "string")))
        }
    )
    @GetMapping("/analytics/by-run/{mlflowRunId}")
    public ResponseEntity<String> getAnalyticsByRun(
            @Parameter(description = "MLflow run ID", example = "abc123def456")
            @PathVariable String mlflowRunId) throws Exception {
        return ResponseEntity.ok(fabric.getDataFetchesByRunId(mlflowRunId));
    }

    // ── Inference ─────────────────────────────────────────────────────────

    @Schema(description = "Request body for recording an inference event on the ledger")
    record InferenceRequest(
        @Schema(description = "Unique inference identifier", example = "inf-001") @NotBlank String inferenceId,
        @Schema(description = "MLflow run ID", example = "abc123def456") @NotBlank String mlflowRunId,
        @Schema(description = "Model name", example = "anomaly-detector") @NotBlank String modelName,
        @Schema(description = "Model version", example = "3") @NotBlank String modelVersion,
        @Schema(description = "Request ID of the analytics record this inference consumed", example = "df-001") @NotBlank String dataFetchRef,
        @Schema(description = "SHA-256 hash of model input tensor", example = "a4f3c9...") @NotBlank String inputHash,
        @Schema(description = "Anomaly score produced by the model", example = "0.87") double anomalyScore,
        @Schema(description = "Model decision label", example = "ANOMALY") @NotBlank String decision
    ) {}

    @Operation(
        summary = "Record an inference event",
        description = "Submits an inference provenance record to the Fabric ledger, linked to a prior analytics record. Returns the transaction ID.",
        responses = {
            @ApiResponse(responseCode = "200", description = "Transaction ID of the submitted record",
                content = @Content(schema = @Schema(type = "string", example = "txid-xyz789"))),
            @ApiResponse(responseCode = "400", description = "Validation error — required fields missing or blank")
        }
    )
    @PostMapping("/inference")
    public ResponseEntity<String> recordInference(@Valid @RequestBody InferenceRequest req)
                                                   throws Exception {
        String result = fabric.recordInference(
            req.inferenceId(), req.mlflowRunId(), req.modelName(), req.modelVersion(),
            req.dataFetchRef(), req.inputHash(), req.anomalyScore(), req.decision());
        return ResponseEntity.ok(result);
    }

    @Operation(
        summary = "Get an inference record by inference ID",
        responses = {
            @ApiResponse(responseCode = "200", description = "JSON-encoded ledger record",
                content = @Content(schema = @Schema(type = "string"))),
            @ApiResponse(responseCode = "404", description = "Record not found")
        }
    )
    @GetMapping("/inference/{inferenceId}")
    public ResponseEntity<String> getInference(
            @Parameter(description = "Inference ID used when the record was created", example = "inf-001")
            @PathVariable String inferenceId) throws Exception {
        try {
            return ResponseEntity.ok(fabric.getInferenceRecord(inferenceId));
        } catch (GatewayException e) {
            if (isNotFound(e)) return ResponseEntity.notFound().build();
            throw e;
        }
    }

    @Operation(
        summary = "Get full provenance for an inference",
        description = "Returns the inference record and the originating analytics record as a single JSON object.",
        responses = {
            @ApiResponse(responseCode = "200", description = "JSON object with 'inference' and 'dataFetch' fields",
                content = @Content(schema = @Schema(type = "string")))
        }
    )
    @GetMapping("/provenance/{inferenceId}")
    public ResponseEntity<String> getProvenance(
            @Parameter(description = "Inference ID to trace", example = "inf-001")
            @PathVariable String inferenceId) throws Exception {
        return ResponseEntity.ok(fabric.getFullProvenance(inferenceId));
    }

    private static boolean isNotFound(GatewayException e) {
        String msg = e.getMessage();
        return msg != null && (msg.contains("NOT_FOUND") || msg.contains("not found") || msg.contains("Record not found"));
    }
}
