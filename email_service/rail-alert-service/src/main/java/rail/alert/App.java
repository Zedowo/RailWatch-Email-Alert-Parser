package rail.alert;

public class App {
    public static void main(String[] args) {
        AlertMessage msg = new AlertMessage(
                "2025-12-06 22:10",
                "Milepost 142.3",
                "Eastbound",
                "Train approaching with defect suspected near joint bar",
                "images/alert_001.jpg"
        )
        ;
        System.out.println(msg);
    }
}