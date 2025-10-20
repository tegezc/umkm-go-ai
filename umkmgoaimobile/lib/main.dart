// File: mobile_app/lib/main.dart

import 'package:flutter/material.dart';
import 'package:umkmgoaimobile/presentation/screens/chat_screen.dart';
import 'package:firebase_core/firebase_core.dart'; // Import
import 'firebase_options.dart';

void main() async{
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'UMKM-Go AI',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const ChatScreen(), // Set ChatScreen sebagai layar utama
      debugShowCheckedModeBanner: false,
    );
  }
}