package org.nwdaf.fabricclient;

import io.grpc.ManagedChannel;
import io.grpc.netty.shaded.io.grpc.netty.GrpcSslContexts;
import io.grpc.netty.shaded.io.grpc.netty.NettyChannelBuilder;
import jakarta.annotation.PreDestroy;
import org.hyperledger.fabric.client.*;
import org.hyperledger.fabric.client.identity.*;
import org.nwdaf.fabricclient.config.FabricConfig;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;

@Service
public class FabricGatewayService {

    private final Gateway gateway;
    private final Network analyticsNetwork;
    private final Network inferenceNetwork;
    private final ManagedChannel grpcChannel;

    public FabricGatewayService(FabricConfig cfg) throws Exception {
        X509Certificate cert = Identities.readX509Certificate(
            Files.newBufferedReader(Path.of(cfg.getMspCertPath())));
        PrivateKey key = Identities.readPrivateKey(
            Files.newBufferedReader(Path.of(cfg.getMspKeyPath())));

        byte[] tlsCert = Files.readAllBytes(Path.of(cfg.getTlsCertPath()));

        grpcChannel = NettyChannelBuilder.forTarget(cfg.getPeerEndpoint())
            .sslContext(GrpcSslContexts.forClient()
                .trustManager(new ByteArrayInputStream(tlsCert)).build())
            .build();

        Identity identity = new X509Identity(cfg.getMspId(), cert);
        Signer signer = Signers.newPrivateKeySigner(key);

        gateway = Gateway.newInstance()
            .identity(identity)
            .signer(signer)
            .connection(grpcChannel)
            .connect();

        analyticsNetwork = gateway.getNetwork(cfg.getAnalyticsChannel());
        inferenceNetwork = gateway.getNetwork(cfg.getInferenceChannel());
    }

    // ── Analytics channel: data fetch records ──────────────────────────────

    public String recordDataFetch(String requestId, String mlflowRunId, String modelName,
                                   String modelVersion, String queryDescriptor, String dataHash,
                                   String timeRangeStart, String timeRangeEnd)
                                   throws GatewayException, CommitException {
        Contract cc = analyticsNetwork.getContract("data-fetch-chaincode");
        byte[] result = cc.submitTransaction("DataFetchChaincode:recordFetch",
            requestId, mlflowRunId, modelName, modelVersion,
            queryDescriptor, dataHash, timeRangeStart, timeRangeEnd);
        return new String(result, StandardCharsets.UTF_8);
    }

    public String getDataFetchRecord(String requestId) throws GatewayException {
        Contract cc = analyticsNetwork.getContract("data-fetch-chaincode");
        byte[] result = cc.evaluateTransaction("DataFetchChaincode:getFetchRecord", requestId);
        return new String(result, StandardCharsets.UTF_8);
    }

    public String getDataFetchesByRunId(String mlflowRunId) throws GatewayException {
        Contract cc = analyticsNetwork.getContract("data-fetch-chaincode");
        byte[] result = cc.evaluateTransaction("DataFetchChaincode:getFetchesByRunId", mlflowRunId);
        return new String(result, StandardCharsets.UTF_8);
    }

    public String getAllDataFetches() throws GatewayException {
        Contract cc = analyticsNetwork.getContract("data-fetch-chaincode");
        byte[] result = cc.evaluateTransaction("DataFetchChaincode:getAllFetches");
        return new String(result, StandardCharsets.UTF_8);
    }

    // ── Inference channel: inference records ────────────────────────────────

    public String recordInference(String inferenceId, String mlflowRunId, String modelName,
                                   String modelVersion, String dataFetchRef, String inputHash,
                                   double anomalyScore, String decision)
                                   throws GatewayException, CommitException {
        Contract cc = inferenceNetwork.getContract("inference-chaincode");
        byte[] result = cc.submitTransaction("InferenceChaincode:recordInference",
            inferenceId, mlflowRunId, modelName, modelVersion,
            dataFetchRef, inputHash, String.valueOf(anomalyScore), decision);
        return new String(result, StandardCharsets.UTF_8);
    }

    public String getInferenceRecord(String inferenceId) throws GatewayException {
        Contract cc = inferenceNetwork.getContract("inference-chaincode");
        byte[] result = cc.evaluateTransaction("InferenceChaincode:getInferenceRecord", inferenceId);
        return new String(result, StandardCharsets.UTF_8);
    }

    public String getAllInferences() throws GatewayException {
        Contract cc = inferenceNetwork.getContract("inference-chaincode");
        byte[] result = cc.evaluateTransaction("InferenceChaincode:getAllInferences");
        return new String(result, StandardCharsets.UTF_8);
    }

    // Full provenance chain: fetches both records and merges them in the sidecar
    // (cross-channel reads aren't possible in chaincode itself)
    public String getFullProvenance(String inferenceId) throws GatewayException {
        String inferenceJson = getInferenceRecord(inferenceId);
        // Extract dataFetchRef from the inference record
        // (simple string extraction — in production use Jackson)
        String dataFetchRef = extractField(inferenceJson, "dataFetchRef");
        String fetchJson = getDataFetchRecord(dataFetchRef);
        return String.format("{\"inference\": %s, \"dataFetch\": %s}",
                              inferenceJson, fetchJson);
    }

    private String extractField(String json, String field) {
        // Minimal extraction — replace with Jackson ObjectMapper in production
        int idx = json.indexOf("\"" + field + "\":");
        if (idx < 0) return "";
        int start = json.indexOf("\"", idx + field.length() + 3) + 1;
        int end = json.indexOf("\"", start);
        return json.substring(start, end);
    }

    @PreDestroy
    public void shutdown() throws InterruptedException {
        gateway.close();
        grpcChannel.shutdownNow();
    }
}
