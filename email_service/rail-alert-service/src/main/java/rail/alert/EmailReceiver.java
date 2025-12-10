package rail.alert;

import com.auxilii.msgparser.Message;
import com.auxilii.msgparser.MsgParser;

import java.io.IOException;
import java.io.File;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

// looks for directory for Outlook .msg files --> converts them into AlertMessage Objects w/ EmailAlertParser
 
public class EmailReceiver {

    private final EmailAlertParser parser;

    public EmailReceiver(EmailAlertParser parser) {
        this.parser = parser;
    }

    private Path createTempFile() throws IOException {
    return java.nio.file.Files.createTempFile("alertEmail", ".txt");
    }

    private void writeToTemp(Path path, String content) throws IOException {
        java.nio.file.Files.writeString(path, content);
    }

    // read all .msg files in folder
    // @param folderPath directory containing .msg exports

    public List<AlertMessage> receive(Path folderPath) {
        List<AlertMessage> results = new ArrayList<>();
        File directory = folderPath.toFile();

        if (!directory.exists() || !directory.isDirectory()) {
            throw new IllegalArgumentException("Invalid Folder Path -- " + folderPath);
        }

        File[] msgFiles = directory.listFiles((dir, name) ->
                name.toLowerCase().endsWith(".msg"));

        if (msgFiles == null) return results;

        MsgParser msgParser = new MsgParser();

        /*
        for each file:
        - parse .msg file into Message object
        - extract body text (ignore HTML)
        - create temporary buffer as .msg is binary and not plain text
        - convert raw email text to alert
        */
        for (File file : msgFiles) {
            try {
                Message msg = msgParser.parseMsg(file);
                String body = msg.getBodyText();

                if (body == null) {
                    System.err.println("Email is empty -- " + file.getName());
                    continue;
                }

                //
                Path temp = createTempFile();
                this.writeToTemp(temp, body);

                AlertMessage alert = parser.parse(temp);
                results.add(alert);

            } catch (Exception ex) {
                System.err.println("File Error -- " + file.getName() + ": " + ex.getMessage());
            }
        }

        return results;
    }
}
