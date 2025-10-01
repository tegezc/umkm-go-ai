// File: mobile_app/lib/presentation/screens/chat_screen.dart

import 'package:flutter/material.dart';
import '../../data/services/api_service.dart';

// A simple class to hold message data
class ChatMessage {
  final String text;
  final bool isUser;

  ChatMessage({required this.text, required this.isUser});
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ApiService _apiService = ApiService();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;

  // --- Core Logic ---
  Future<void> _sendMessage() async {
    final String query = _textController.text;
    if (query.isEmpty) return;

    // Add user message to the list
    setState(() {
      _messages.add(ChatMessage(text: query, isUser: true));
      _isLoading = true;
    });
    _textController.clear();

    try {
      // For now, we'll hardcode to call the Legal Agent
      // In the future, we can add a switch/tab to select an agent.
      final response = await _apiService.askLegalAgent(query);

      final String answer = response['answer'] ?? "No answer found.";

      // Add AI response to the list
      setState(() {
        _messages.add(ChatMessage(text: answer, isUser: false));
      });

    } catch (e) {
      // Handle errors
      setState(() {
        _messages.add(ChatMessage(text: "Error: ${e.toString()}", isUser: false));
      });
    } finally {
      // Stop loading indicator
      setState(() {
        _isLoading = false;
      });
    }
  }

  // --- UI Building ---
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('UMKM-Go AI'),
        backgroundColor: Colors.blueAccent,
      ),
      body: Column(
        children: [
          // Chat messages area
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildChatBubble(message);
              },
            ),
          ),
          // Loading indicator
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          // Input area
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildChatBubble(ChatMessage message) {
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 5.0, horizontal: 8.0),
        padding: const EdgeInsets.all(12.0),
        decoration: BoxDecoration(
          color: message.isUser ? Colors.blue[300] : Colors.grey[200],
          borderRadius: BorderRadius.circular(15.0),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: message.isUser ? Colors.white : Colors.black87,
          ),
        ),
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.3),
            spreadRadius: 2,
            blurRadius: 5,
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: const InputDecoration.collapsed(
                hintText: 'Tanyakan sesuatu...',
              ),
              onSubmitted: (value) => _sendMessage(),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send, color: Colors.blueAccent),
            onPressed: _isLoading ? null : _sendMessage,
          ),
        ],
      ),
    );
  }
}