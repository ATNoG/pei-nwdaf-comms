package org.nwdaf.chaincode;

import com.owlike.genson.Genson;
import org.hyperledger.fabric.contract.Context;
import org.hyperledger.fabric.contract.ContractInterface;
import org.hyperledger.fabric.contract.annotation.Contract;
import org.hyperledger.fabric.contract.annotation.Default;
import org.hyperledger.fabric.contract.annotation.Info;
import org.hyperledger.fabric.contract.annotation.Transaction;
import org.hyperledger.fabric.shim.ChaincodeException;
import org.hyperledger.fabric.shim.ChaincodeStub;
import org.hyperledger.fabric.shim.ledger.KeyValue;
import org.hyperledger.fabric.shim.ledger.QueryResultsIterator;

import java.util.ArrayList;
import java.util.List;

@Contract(
    name = "DataFetchChaincode",
    info = @Info(title = "NWDAF Data Fetch Ledger", version = "1.0")
)
@Default
public final class DataFetchChaincode implements ContractInterface {

    private final Genson genson = new Genson();

    @Transaction(intent = Transaction.TYPE.SUBMIT)
    public DataFetchRecord recordFetch(final Context ctx,
                                       final String requestId,
                                       final String mlflowRunId,
                                       final String modelName,
                                       final String modelVersion,
                                       final String queryDescriptor,
                                       final String dataHash,
                                       final String cellIds,
                                       final String timeRangeStart,
                                       final String timeRangeEnd) {
        ChaincodeStub stub = ctx.getStub();

        String existing = stub.getStringState(requestId);
        if (existing != null && !existing.isEmpty()) {
            throw new ChaincodeException(
                "Fetch record " + requestId + " already exists", "ALREADY_EXISTS");
        }

        DataFetchRecord record = new DataFetchRecord(
            requestId, mlflowRunId, modelName, modelVersion,
            queryDescriptor, dataHash, cellIds, timeRangeStart, timeRangeEnd,
            stub.getTxTimestamp().toString()
        );

        stub.putStringState(requestId, genson.serialize(record));
        stub.setEvent("DataFetched", genson.serialize(record).getBytes());

        return record;
    }

    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public DataFetchRecord getFetchRecord(final Context ctx, final String requestId) {
        String json = ctx.getStub().getStringState(requestId);
        if (json == null || json.isEmpty()) {
            throw new ChaincodeException("Record not found: " + requestId, "NOT_FOUND");
        }
        return genson.deserialize(json, DataFetchRecord.class);
    }

    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public String getFetchesByModel(final Context ctx, final String modelName) {
        String query = String.format(
            "{\"selector\":{\"modelName\":\"%s\"},\"sort\":[{\"timestamp\":\"desc\"}],\"limit\":100}",
            modelName);
        return runRichQuery(ctx, query);
    }

    @Transaction(intent = Transaction.TYPE.EVALUATE)
    public String getFetchesByRunId(final Context ctx, final String mlflowRunId) {
        String query = String.format(
            "{\"selector\":{\"mlflowRunId\":\"%s\"}}", mlflowRunId);
        return runRichQuery(ctx, query);
    }

    private String runRichQuery(final Context ctx, final String query) {
        QueryResultsIterator<KeyValue> results = ctx.getStub().getQueryResult(query);
        List<DataFetchRecord> records = new ArrayList<>();
        for (KeyValue kv : results) {
            records.add(genson.deserialize(kv.getStringValue(), DataFetchRecord.class));
        }
        return genson.serialize(records);
    }
}
