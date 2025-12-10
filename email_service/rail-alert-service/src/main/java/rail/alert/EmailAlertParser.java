package rail.alert;

import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;

public class EmailAlertParser {

    /*string markers format in email text

    data should be as follows:

    Time of detection: YYYY-MM-DD HR:MIN
    Location: x
    Direction: E/W
    
    */
    private static final String TIME_PREFIX = "Time of detection:";
    private static final String LOCATION_PREFIX = "Location:";
    private static final String DIRECTION_PREFIX = "Direction:";

    public AlertMessage parse(Path filePath) {
        try {
            // read email in one string
            String text = Files.readString(filePath);

            String time = extractAfter(text, TIME_PREFIX);
            String location = extractAfter(text, LOCATION_PREFIX);
            String direction = extractAfter(text, DIRECTION_PREFIX);

            // if not found (possible for some .msg files, should be standarized however)
            if (time == null) time = "UNKNOWN";
            if (location == null) location = "UNKNOWN";
            if (direction == null) direction = "UNKNOWN";

            return new AlertMessage(time, location, direction, text, filePath.toString(), "", filePath.getFileName().toString());

        } catch (IOException e) {
            System.err.println("Could not read -- " + filePath);
            throw new RuntimeException(e);
        }
    }

    // find line with specified prefix
    private String extractAfter(String text, String prefix) {
        for (String line : text.split("\n")) {
            if (line.trim().startsWith(prefix)) {
                return line.substring(prefix.length()).trim();
            }
        }
        return null;
    }
}