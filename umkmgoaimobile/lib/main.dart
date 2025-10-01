// File: mobile_app/lib/main.dart

import 'package:flutter/material.dart';
import 'package:umkmgoaimobile/presentation/screens/chat_screen.dart';

void main() {
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