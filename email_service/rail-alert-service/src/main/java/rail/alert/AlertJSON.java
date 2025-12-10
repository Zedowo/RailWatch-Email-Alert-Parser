package rail.alert;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.util.List;

public class AlertJSON {

    private final Gson gson;

    public AlertJSON() {
        // pretty print for easier debugging
        this.gson = new GsonBuilder()
                .setPrettyPrinting()
                .create();
    }

    //convert one AlertMessage to JSON str
    public String toJson(AlertMessage alert) {
        return gson.toJson(alert);
    }

    public String toJson(List<AlertMessage> alerts) {
        return gson.toJson(alerts);
    }
}
