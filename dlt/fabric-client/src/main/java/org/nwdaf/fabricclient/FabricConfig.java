package org.nwdaf.fabricclient.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "fabric")
public class FabricConfig {
    private String peerEndpoint;
    private String analyticsChannel;
    private String inferenceChannel;
    private String mspId;
    private String mspCertPath;
    private String mspKeyPath;
    private String tlsCertPath;

    // getters and setters for all fields
    public String getPeerEndpoint() { return peerEndpoint; }
    public void setPeerEndpoint(String v) { this.peerEndpoint = v; }
    public String getAnalyticsChannel() { return analyticsChannel; }
    public void setAnalyticsChannel(String v) { this.analyticsChannel = v; }
    public String getInferenceChannel() { return inferenceChannel; }
    public void setInferenceChannel(String v) { this.inferenceChannel = v; }
    public String getMspId() { return mspId; }
    public void setMspId(String v) { this.mspId = v; }
    public String getMspCertPath() { return mspCertPath; }
    public void setMspCertPath(String v) { this.mspCertPath = v; }
    public String getMspKeyPath() { return mspKeyPath; }
    public void setMspKeyPath(String v) { this.mspKeyPath = v; }
    public String getTlsCertPath() { return tlsCertPath; }
    public void setTlsCertPath(String v) { this.tlsCertPath = v; }
}
