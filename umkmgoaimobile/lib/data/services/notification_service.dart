// File: mobile_app/lib/data/services/notification_service.dart

import 'package:firebase_messaging/firebase_messaging.dart';

class NotificationService {
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;

  Future<void> initNotifications() async {
    // 1. Request permission from the user (important for iOS & Android 13+)
    await _firebaseMessaging.requestPermission();

    // 2. Get the FCM Token for this device
    final fcmToken = await _firebaseMessaging.getToken();

    // 3. Print the token to the console
    // THIS IS THE TOKEN WE NEED FOR THE BACKEND
    print("====================================================");
    print("|| FCM Device Token: $fcmToken ||");
    print("====================================================");

    // 4. Set up a listener for messages that arrive while the app is in the foreground
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('Foreground message received!');
      if (message.notification != null) {
        print('Notification Title: ${message.notification!.title}');
        print('Notification Body: ${message.notification!.body}');
      }
    });
  }
}