package org.nwdaf.chaincode;

import org.hyperledger.fabric.contract.annotation.DataType;
import org.hyperledger.fabric.contract.annotation.Property;
import com.owlike.genson.annotation.JsonProperty;

@DataType()
public class InferenceRecord {

    @Property()
    @JsonProperty("inferenceId")
    private String inferenceId;

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
    @JsonProperty("dataFetchRef")
    private String dataFetchRef;

    @Property()
    @JsonProperty("inputHash")
    private String inputHash;

    @Property()
    @JsonProperty("anomalyScore")
    private double anomalyScore;

    @Property()
    @JsonProperty("decision")
    private String decision;

    @Property()
    @JsonProperty("timestamp")
    private String timestamp;

    public InferenceRecord() {}

    public InferenceRecord(String inferenceId, String mlflowRunId, String modelName,
                           String modelVersion, String dataFetchRef, String inputHash,
                           double anomalyScore, String decision, String timestamp) {
        this.inferenceId = inferenceId;
        this.mlflowRunId = mlflowRunId;
        this.modelName = modelName;
        this.modelVersion = modelVersion;
        this.dataFetchRef = dataFetchRef;
        this.inputHash = inputHash;
        this.anomalyScore = anomalyScore;
        this.decision = decision;
        this.timestamp = timestamp;
    }

    public String getInferenceId()  { return inferenceId; }
    public String getMlflowRunId()  { return mlflowRunId; }
    public String getModelName()    { return modelName; }
    public String getModelVersion() { return modelVersion; }
    public String getDataFetchRef() { return dataFetchRef; }
    public String getInputHash()    { return inputHash; }
    public double getAnomalyScore() { return anomalyScore; }
    public String getDecision()     { return decision; }
    public String getTimestamp()    { return timestamp; }
}
