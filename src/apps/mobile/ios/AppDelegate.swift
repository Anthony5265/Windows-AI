import UIKit
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
        return true
    }

    func showNotification(_ message: String) {
        let content = UNMutableNotificationContent()
        content.title = "Windows AI"
        content.body = message
        let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request, withCompletionHandler: nil)
    }

    func pair(deviceId: String, completion: @escaping (String?) -> Void) {
        var request = URLRequest(url: URL(string: "http://localhost:3000/api/mobile/pair")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{\"deviceId\":\"\(deviceId)\"}".data(using: .utf8)
        URLSession.shared.dataTask(with: request) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let token = json["token"] as? String else {
                completion(nil)
                return
            }
            completion(token)
        }.resume()
    }

    func sendCommand(token: String, action: String) {
        var request = URLRequest(url: URL(string: "http://localhost:3000/api/mobile/command")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{\"token\":\"\(token)\",\"action\":\"\(action)\"}".data(using: .utf8)
        URLSession.shared.dataTask(with: request).resume()
    }
}
