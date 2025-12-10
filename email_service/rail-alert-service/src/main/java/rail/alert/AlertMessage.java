package rail.alert;

public class AlertMessage {
    private final String msgId;            
    private final String originalFilename; 
    private final String timestamp;
    private final String location;
    private final String direction;
    private final String rawText;
    private final String imagePath;

    public AlertMessage(String timestamp, String location, String direction,
                        String rawText, String imagePath,
                        String msgId, String originalFilename) {
        this.timestamp = timestamp;
        this.location = location;
        this.direction = direction;
        this.rawText = rawText;
        this.imagePath = imagePath;
        this.msgId = msgId;
        this.originalFilename = originalFilename;
    }

    public String getMsgId() { return msgId; }
    public String getOriginalFilename() { return originalFilename; }
    public String getTimestamp() { return timestamp; }
    public String getLocation() { return location; }
    public String getDirection() { return direction; }
    public String getRawText() { return rawText; }
    public String getImagePath() { return imagePath; }

    @Override
    public String toString() {
        return "AlertMessage{" +
                "msgId='" + msgId + '\'' +
                ", originalFilename='" + originalFilename + '\'' +
                ", timestamp='" + timestamp + '\'' +
                ", location='" + location + '\'' +
                ", direction='" + direction + '\'' +
                ", rawText='" + rawText + '\'' +
                ", imagePath='" + imagePath + '\'' +
                '}';
    }
}