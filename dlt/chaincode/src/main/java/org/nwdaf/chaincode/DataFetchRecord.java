package org.nwdaf.chaincode;

import org.hyperledger.fabric.contract.annotation.DataType;
import org.hyperledger.fabric.contract.annotation.Property;
import com.owlike.genson.annotation.JsonProperty;

@DataType()
public class DataFetchRecord {

    @Property()
    @JsonProperty("requestId")
    private String requestId;

    @Property()
    @JsonProperty("mlflowRunId")
    private String mlflowRunId;

    @Property()
    @JsonProperty("modelName")
    private String modelName;

    @Property()
    @JsonProperty("modelVersion")
    private String modelVersion;

    @Property()
    @JsonProperty("queryDescriptor")
    private String queryDescriptor;

    @Property()
    @JsonProperty("dataHash")
    private String dataHash;

    @Property()
    @JsonProperty("cellIds")
    private String cellIds;

    @Property()
    @JsonProperty("timeRangeStart")
    private String timeRangeStart;

    @Property()
    @JsonProperty("timeRangeEnd")
    private String timeRangeEnd;

    @Property()
    @JsonProperty("timestamp")
    private String timestamp;

    public DataFetchRecord() {}

    public DataFetchRecord(String requestId, String mlflowRunId, String modelName,
                           String modelVersion, String queryDescriptor, String dataHash,
                           String cellIds, String timeRangeStart, String timeRangeEnd,
                           String timestamp) {
        this.requestId = requestId;
        this.mlflowRunId = mlflowRunId;
        this.modelName = modelName;
        this.modelVersion = modelVersion;
        this.queryDescriptor = queryDescriptor;
        this.dataHash = dataHash;
        this.cellIds = cellIds;
        this.timeRangeStart = timeRangeStart;
        this.timeRangeEnd = timeRangeEnd;
        this.timestamp = timestamp;
    }

    public String getRequestId()       { return requestId; }
    public String getMlflowRunId()     { return mlflowRunId; }
    public String getModelName()       { return modelName; }
    public String getModelVersion()    { return modelVersion; }
    public String getQueryDescriptor() { return queryDescriptor; }
    public String getDataHash()        { return dataHash; }
    public String getCellIds()         { return cellIds; }
    public String getTimeRangeStart()  { return timeRangeStart; }
    public String getTimeRangeEnd()    { return timeRangeEnd; }
    public String getTimestamp()       { return timestamp; }
}
