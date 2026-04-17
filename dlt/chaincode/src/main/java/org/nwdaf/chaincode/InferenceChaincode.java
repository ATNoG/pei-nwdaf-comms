package org.nwdaf.chaincode;

import com.owlike.genson.Genson;
import org.hyperledger.fabric.contract.Context;
import org.hyperledger.fabric.contract.ContractInterface;
import org.hyperledger.fabric.contract.annotation.Contract;
import org.hyperledger.fabric.contract.annotation.Info;
import org.hyperledger.fabric.contract.annotation.Transaction;
import org.hyperledger.fabric.shim.ChaincodeException;
import org.hyperledger.fabric.shim.ChaincodeStub;
import org.hyperledger.fabric.shim.ledger.KeyValue;
import org.hyperledger.fabric.shim.ledger.QueryResultsIterator;

import java.util.ArrayList;
import java.util.List;

@Contract(
    name = "InferenceChaincode",
    info = @Info(title = "NWDAF Inference Ledger", version = "1.0")
)
public final class InferenceChaincode implements ContractInterface {

    private final Genson genson = new Genson();

    @Transaction(intent = Transaction.TYPE.SUBMIT)
    public InferenceRecord recordInference(final Context ctx,
                                           final String inferenceId,
                                           final String mlflowRunId,
                                           final String modelName,
                                           final String modelVersion,
                                           final String dataFetchRef,
                                           final String inputHash,
                                           final String anomalyScoreStr,
                                           final String decision) {
        ChaincodeStub stub = ctx.getStub();

        String existing = stub.getStringState(inferenceId);
        if (existing != null && !existing.isEmpty()) {
            throw new ChaincodeException(
                "Inference record already exists: " + inferenceId, "ALREADY_EXISTS");
        }

        double anomalyScore;
        try {
            anomalyScore = Double.parseDouble(anomalyScoreStr);
        } catch (NumberFormatException e) {
            throw new ChaincodeException(
                "Invalid anomalyScore value: " + anomalyScoreStr, "INVALID_INPUT");
        }

        InferenceRecord record = new InferenceRecord(
            inferenceId, mlflowRunId, modelName, modelVersion,
            dataFetchRef, inputHash, anomalyScore, decision,
            stub.getTxTimestamp().toString()
        );

        stub.putStringState(inferenceId, genson.serialize(record));
        stub.setEvent("InferenceRecorded", genson.serialize(record).getBytes());

        return record;
    }

    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public InferenceRecord getInferenceRecord(final Context ctx, final String inferenceId) {
        String json = ctx.getStub().getStringState(inferenceId);
        if (json == null || json.isEmpty()) {
            throw new ChaincodeException("Record not found: " + inferenceId, "NOT_FOUND");
        }
        return genson.deserialize(json, InferenceRecord.class);
    }

    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public String getInferencesByModel(final Context ctx, final String modelName) {
        String query = String.format(
            "{\"selector\":{\"modelName\":\"%s\"},\"sort\":[{\"timestamp\":\"desc\"}],\"limit\":100}",
            modelName);
        return runRichQuery(ctx, query);
    }

    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public String getInferencesByRunId(final Context ctx, final String mlflowRunId) {
        String query = String.format(
            "{\"selector\":{\"mlflowRunId\":\"%s\"}}", mlflowRunId);
        return runRichQuery(ctx, query);
    }

    // Returns the inference record JSON — the sidecar fetches the linked
    // DataFetch record from analytics-channel separately (cross-channel reads
    // are not permitted within chaincode itself).
    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public String getProvenanceRef(final Context ctx, final String inferenceId) {
        String json = ctx.getStub().getStringState(inferenceId);
        if (json == null || json.isEmpty()) {
            throw new ChaincodeException("Record not found: " + inferenceId, "NOT_FOUND");
        }
        InferenceRecord record = genson.deserialize(json, InferenceRecord.class);
        return String.format(
            "{\"inferenceId\":\"%s\",\"dataFetchRef\":\"%s\",\"mlflowRunId\":\"%s\"}",
            record.getInferenceId(), record.getDataFetchRef(), record.getMlflowRunId());
    }

    private String runRichQuery(final Context ctx, final String query) {
        QueryResultsIterator<KeyValue> results = ctx.getStub().getQueryResult(query);
        List<InferenceRecord> records = new ArrayList<>();
        for (KeyValue kv : results) {
            records.add(genson.deserialize(kv.getStringValue(), InferenceRecord.class));
        }
        return genson.serialize(records);
    }
}
