package rail.alert;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

public class RailAlertService {

    public static void main(String[] args) {

        if (args.length < 2) {
                System.out.println("Format: java -jar rail-alert-service.jar <inputFolder> <outputFolder>");
                return;
            }

        Path inputPath = Path.of(args[0]); 
        Path outputPath = Path.of(args[1]);

        EmailReceiver receiver = new EmailReceiver(new EmailAlertParser());
        List<AlertMessage> alerts = receiver.receive(inputPath);
        AlertJSON json = new AlertJSON();
        String output = json.toJson(alerts);

        //all JSON saved as one file
        saveJson(outputPath, "alerts.json", output);
        System.out.println("Saved JSON to -- " + outputPath.resolve("alerts.json"));
    }

public static void saveJson(Path folder, String filename, String json) {
        try {
            Files.createDirectories(folder); // make folder if missing
            Path outPath = folder.resolve(filename);
            Files.writeString(outPath, json);
        } catch (Exception e) {
            throw new RuntimeException("JSON write unsucessful -- ", e);
        }
    }
}

