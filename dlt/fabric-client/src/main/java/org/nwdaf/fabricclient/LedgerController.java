package org.nwdaf.fabricclient.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.hyperledger.fabric.client.GatewayException;
import org.nwdaf.fabricclient.FabricGatewayService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/ledger")
public class LedgerController {

    private final FabricGatewayService fabric;

    public LedgerController(FabricGatewayService fabric) {
        this.fabric = fabric;
    }

    // ── Data fetch ────────────────────────────────────────────────────────

    record DataFetchRequest(
        @NotBlank String requestId,
        @NotBlank String mlflowRunId,
        @NotBlank String modelName,
        @NotBlank String modelVersion,
        @NotBlank String queryDescriptor,
        @NotBlank String dataHash,
        String cellIds,
        String timeRangeStart,
        String timeRangeEnd
    ) {}

    @PostMapping("/data-fetch")
    public ResponseEntity<String> recordDataFetch(@Valid @RequestBody DataFetchRequest req)
                                                   throws Exception {
        String result = fabric.recordDataFetch(
            req.requestId(), req.mlflowRunId(), req.modelName(), req.modelVersion(),
            req.queryDescriptor(), req.dataHash(),
            req.cellIds(), req.timeRangeStart(), req.timeRangeEnd());
        return ResponseEntity.ok(result);
    }

    @GetMapping("/data-fetch/{requestId}")
    public ResponseEntity<String> getDataFetch(@PathVariable String requestId) throws Exception {
        try {
            return ResponseEntity.ok(fabric.getDataFetchRecord(requestId));
        } catch (GatewayException e) {
            if (isNotFound(e)) return ResponseEntity.notFound().build();
            throw e;
        }
    }

    @GetMapping("/data-fetch/by-run/{mlflowRunId}")
    public ResponseEntity<String> getDataFetchesByRun(@PathVariable String mlflowRunId)
                                                       throws Exception {
        return ResponseEntity.ok(fabric.getDataFetchesByRunId(mlflowRunId));
    }

    // ── Inference ─────────────────────────────────────────────────────────

    record InferenceRequest(
        @NotBlank String inferenceId,
        @NotBlank String mlflowRunId,
        @NotBlank String modelName,
        @NotBlank String modelVersion,
        @NotBlank String dataFetchRef,
        @NotBlank String inputHash,
        double anomalyScore,
        @NotBlank String decision
    ) {}

    @PostMapping("/inference")
    public ResponseEntity<String> recordInference(@Valid @RequestBody InferenceRequest req)
                                                   throws Exception {
        String result = fabric.recordInference(
            req.inferenceId(), req.mlflowRunId(), req.modelName(), req.modelVersion(),
            req.dataFetchRef(), req.inputHash(), req.anomalyScore(), req.decision());
        return ResponseEntity.ok(result);
    }

    @GetMapping("/inference/{inferenceId}")
    public ResponseEntity<String> getInference(@PathVariable String inferenceId) throws Exception {
        try {
            return ResponseEntity.ok(fabric.getInferenceRecord(inferenceId));
        } catch (GatewayException e) {
            if (isNotFound(e)) return ResponseEntity.notFound().build();
            throw e;
        }
    }

    // Full provenance: inference + its originating data fetch
    @GetMapping("/provenance/{inferenceId}")
    public ResponseEntity<String> getProvenance(@PathVariable String inferenceId) throws Exception {
        return ResponseEntity.ok(fabric.getFullProvenance(inferenceId));
    }

    private static boolean isNotFound(GatewayException e) {
        String msg = e.getMessage();
        return msg != null && (msg.contains("NOT_FOUND") || msg.contains("not found") || msg.contains("Record not found"));
    }
}
